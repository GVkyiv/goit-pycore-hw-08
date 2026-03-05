from __future__ import annotations

from collections import UserDict
from datetime import date, datetime, timedelta
from functools import wraps
import pickle
from typing import Any, Callable, TypeVar

# РЈР·Р°РіР°Р»СЊРЅРµРЅРёР№ С‚РёРї РґР»СЏ РґРµРєРѕСЂР°С‚РѕСЂР°: РїСЂРёР№РјР°С” С„СѓРЅРєС†С–СЋ, С‰Рѕ РїРѕРІРµСЂС‚Р°С” str
T = TypeVar("T", bound=Callable[..., str])
DATA_FILE = "addressbook.pkl"


class Field:
    """
    Р‘Р°Р·РѕРІРёР№ РєР»Р°СЃ РґР»СЏ РІСЃС–С… РїРѕР»С–РІ (Name, Phone, Birthday С‚РѕС‰Рѕ).
    Р—Р±РµСЂС–РіР°С” Р·РЅР°С‡РµРЅРЅСЏ С‚Р° РґРѕР·РІРѕР»СЏС” РіР°СЂРЅРѕ РІРёРІРѕРґРёС‚Рё Р№РѕРіРѕ СЏРє СЂСЏРґРѕРє.
    """
    value: Any

    def __init__(self, value: Any) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    """РџРѕР»Рµ РґР»СЏ Р·Р±РµСЂС–РіР°РЅРЅСЏ С–РјРµРЅС– РєРѕРЅС‚Р°РєС‚Сѓ."""
    pass


class Phone(Field):
    """
    РџРѕР»Рµ РґР»СЏ Р·Р±РµСЂС–РіР°РЅРЅСЏ С‚РµР»РµС„РѕРЅСѓ.
    Р’Р°Р»С–РґР°С†С–СЏ: С‚РµР»РµС„РѕРЅ РјР°С” Р±СѓС‚Рё СЂСЏРґРєРѕРј Р· СЂС–РІРЅРѕ 10 С†РёС„СЂ.
    """

    def __init__(self, value: str) -> None:
        if not isinstance(value, str) or not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    """
    РџРѕР»Рµ РґР»СЏ РґР°С‚Рё РЅР°СЂРѕРґР¶РµРЅРЅСЏ.
    Р’Р°Р»С–РґР°С†С–СЏ: С„РѕСЂРјР°С‚ DD.MM.YYYY.
    РЈСЃРµСЂРµРґРёРЅС– Р·Р±РµСЂС–РіР°С”РјРѕ РЅРµ СЂСЏРґРѕРє, Р° РѕР±вЂ™С”РєС‚ date (Р·СЂСѓС‡РЅС–С€Рµ РґР»СЏ СЂРѕР·СЂР°С…СѓРЅРєС–РІ).
    """

    def __init__(self, value: str) -> None:
        try:
            parsed_date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError as error:
            # РџС–РґРЅС–РјР°С”РјРѕ "Р»СЋРґСЃСЊРєСѓ" РїРѕРјРёР»РєСѓ Р· РїСЂР°РІРёР»СЊРЅРёРј РїРѕРІС–РґРѕРјР»РµРЅРЅСЏРј
            raise ValueError("Invalid date format. Use DD.MM.YYYY") from error
        super().__init__(parsed_date)

    def __str__(self) -> str:
        # РџСЂРё РІРёРІРµРґРµРЅРЅС– РЅР°Р·Р°Рґ РїРѕРєР°Р·СѓС”РјРѕ СЏРє DD.MM.YYYY
        return self.value.strftime("%d.%m.%Y")


class Record:
    """
    Р—Р°РїРёСЃ Р°РґСЂРµСЃРЅРѕС— РєРЅРёРіРё: С–Рј'СЏ, СЃРїРёСЃРѕРє С‚РµР»РµС„РѕРЅС–РІ, (РѕРїС†С–Р№РЅРѕ) РґРµРЅСЊ РЅР°СЂРѕРґР¶РµРЅРЅСЏ.
    """

    def __init__(self, name: str) -> None:
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday | None = None

    def add_phone(self, phone: str) -> None:
        # Р”РѕРґР°С”РјРѕ С‚РµР»РµС„РѕРЅ, РїСЂРё СЃС‚РІРѕСЂРµРЅРЅС– Phone РІС–РґР±СѓРґРµС‚СЊСЃСЏ РІР°Р»С–РґР°С†С–СЏ
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> None:
        # Р’РёРґР°Р»СЏС”РјРѕ С‚РµР»РµС„РѕРЅ, СЏРєС‰Рѕ Р№РѕРіРѕ РЅРµ Р·РЅР°Р№РґРµРЅРѕ вЂ” РїРѕРјРёР»РєР°
        phone_to_remove = self.find_phone(phone)
        if phone_to_remove is None:
            raise ValueError("Phone number not found.")
        self.phones.remove(phone_to_remove)

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        # Р—РЅР°С…РѕРґРёРјРѕ СЃС‚Р°СЂРёР№ С‚РµР»РµС„РѕРЅ С– Р·Р°РјС–РЅСЋС”РјРѕ Р№РѕРіРѕ Р·РЅР°С‡РµРЅРЅСЏРј РЅРѕРІРѕРіРѕ
        phone_to_edit = self.find_phone(old_phone)
        if phone_to_edit is None:
            raise ValueError("Phone number not found.")
        # Р’Р°Р¶Р»РёРІРѕ: РЅРѕРІРёР№ РЅРѕРјРµСЂ С‚Р°РєРѕР¶ РїРµСЂРµРІС–СЂСЏС”С‚СЊСЃСЏ С‡РµСЂРµР· Phone(...)
        phone_to_edit.value = Phone(new_phone).value

    def find_phone(self, phone: str) -> Phone | None:
        # РџРѕРІРµСЂС‚Р°С”РјРѕ РѕР±'С”РєС‚ Phone, СЏРєС‰Рѕ Р·РЅР°Р№РґРµРЅРѕ, Р°Р±Рѕ None
        for saved_phone in self.phones:
            if saved_phone.value == phone:
                return saved_phone
        return None

    def add_birthday(self, birthday: str) -> None:
        # Р”РѕРґР°С”РјРѕ/РѕРЅРѕРІР»СЋС”РјРѕ РґРµРЅСЊ РЅР°СЂРѕРґР¶РµРЅРЅСЏ (РІР°Р»С–РґРЅС–СЃС‚СЊ РїРµСЂРµРІС–СЂСЏС” Birthday)
        self.birthday = Birthday(birthday)

    def __str__(self) -> str:
        # Р¤РѕСЂРјСѓС”РјРѕ Р·СЂСѓС‡РЅРёР№ СЂСЏРґРѕРє РґР»СЏ РІРёРІРѕРґСѓ Р·Р°РїРёСЃСѓ
        phones = "; ".join(phone.value for phone in self.phones) or "no phones"
        birthday = str(self.birthday) if self.birthday else "not set"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"


class AddressBook(UserDict):
    """
    РђРґСЂРµСЃРЅР° РєРЅРёРіР° вЂ” С†Рµ СЃР»РѕРІРЅРёРє (name -> Record).
    РќР°СЃР»С–РґСѓС”РјРѕСЃСЊ РІС–Рґ UserDict, С‰РѕР± РјР°С‚Рё СЃС‚Р°РЅРґР°СЂС‚РЅСѓ РїРѕРІРµРґС–РЅРєСѓ СЃР»РѕРІРЅРёРєР°.
    """

    data: dict[str, Record]

    def add_record(self, record: Record) -> None:
        # Р”РѕРґР°С”РјРѕ Р·Р°РїРёСЃ Сѓ СЃР»РѕРІРЅРёРє Р·Р° РєР»СЋС‡РµРј С–РјРµРЅС–
        self.data[record.name.value] = record

    def find(self, name: str) -> Record | None:
        # РЁСѓРєР°С”РјРѕ Р·Р°РїРёСЃ Р·Р° С–РјвЂ™СЏРј. РЇРєС‰Рѕ РЅРµРјР° вЂ” None
        return self.data.get(name)

    def delete(self, name: str) -> None:
        # Р’РёРґР°Р»СЏС”РјРѕ Р·Р°РїРёСЃ Р·Р° С–РјвЂ™СЏРј, СЏРєС‰Рѕ РІС–РЅ С–СЃРЅСѓС”
        if name in self.data:
            del self.data[name]

    @staticmethod
    def _get_birthday_for_year(birthday: date, year: int) -> date:
        try:
            return birthday.replace(year=year)
        except ValueError:
            return date(year, 2, 28)

    def get_upcoming_birthdays(self) -> list[dict[str, str]]:
        """
        РџРѕРІРµСЂС‚Р°С” СЃРїРёСЃРѕРє Р»СЋРґРµР№, СЏРєРёС… С‚СЂРµР±Р° РїСЂРёРІС–С‚Р°С‚Рё РїСЂРѕС‚СЏРіРѕРј РЅР°СЃС‚СѓРїРЅРёС… 7 РґРЅС–РІ.
        РЇРєС‰Рѕ РґРµРЅСЊ РЅР°СЂРѕРґР¶РµРЅРЅСЏ РїСЂРёРїР°РґР°С” РЅР° РІРёС…С–РґРЅС– (РЎР±/РќРґ),
        РґР°С‚Р° РїСЂРёРІС–С‚Р°РЅРЅСЏ РїРµСЂРµРЅРѕСЃРёС‚СЊСЃСЏ РЅР° РЅР°Р№Р±Р»РёР¶С‡РёР№ РїРѕРЅРµРґС–Р»РѕРє.
        """
        today = date.today()
        upcoming_birthdays: list[dict[str, str]] = []

        for record in self.data.values():
            # РџСЂРѕРїСѓСЃРєР°С”РјРѕ РєРѕРЅС‚Р°РєС‚Рё Р±РµР· РґРЅСЏ РЅР°СЂРѕРґР¶РµРЅРЅСЏ
            if record.birthday is None:
                continue

            # Р”РµРЅСЊ РЅР°СЂРѕРґР¶РµРЅРЅСЏ С†СЊРѕРіРѕ СЂРѕРєСѓ (С‚С–Р»СЊРєРё РґРµРЅСЊ/РјС–СЃСЏС†СЊ, СЂС–Рє = РїРѕС‚РѕС‡РЅРёР№)
            birthday_this_year = self._get_birthday_for_year(record.birthday.value, today.year)

            # РЇРєС‰Рѕ РІР¶Рµ РјРёРЅСѓРІ Сѓ С†СЊРѕРјСѓ СЂРѕС†С– вЂ” Р±РµСЂРµРјРѕ РЅР°СЃС‚СѓРїРЅРёР№ СЂС–Рє
            if birthday_this_year < today:
                birthday_this_year = self._get_birthday_for_year(
                    record.birthday.value, today.year + 1
                )

            # РЎРєС–Р»СЊРєРё РґРЅС–РІ Р·Р°Р»РёС€РёР»РѕСЃСЊ РґРѕ Р”Рќ
            days_until_birthday = (birthday_this_year - today).days

            # Р‘РµСЂРµРјРѕ С‚С–Р»СЊРєРё РЅР°СЃС‚СѓРїРЅРёР№ С‚РёР¶РґРµРЅСЊ (0..7)
            if days_until_birthday > 7:
                continue

            # Р”Р°С‚Р° РїСЂРёРІС–С‚Р°РЅРЅСЏ: Р·Р° Р·Р°РјРѕРІС‡СѓРІР°РЅРЅСЏРј СЃР°РјР° РґР°С‚Р° Р”Рќ
            congratulation_date = birthday_this_year

            # РЇРєС‰Рѕ С†Рµ СЃСѓР±РѕС‚Р° (5) Р°Р±Рѕ РЅРµРґС–Р»СЏ (6) вЂ” РїРµСЂРµРЅРѕСЃРёРјРѕ РЅР° РїРѕРЅРµРґС–Р»РѕРє
            if congratulation_date.weekday() >= 5:
                congratulation_date += timedelta(days=7 - congratulation_date.weekday())

            upcoming_birthdays.append(
                {
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime("%d.%m.%Y"),
                }
            )

        # РЎРѕСЂС‚СѓС”РјРѕ Р·Р° РґР°С‚РѕСЋ РїСЂРёРІС–С‚Р°РЅРЅСЏ
        return sorted(
            upcoming_birthdays,
            key=lambda item: datetime.strptime(item["congratulation_date"], "%d.%m.%Y"),
        )


def input_error(func: T) -> T:
    """
    Р”РµРєРѕСЂР°С‚РѕСЂ РґР»СЏ РѕР±СЂРѕР±РєРё РїРѕРјРёР»РѕРє РІРІРµРґРµРЅРЅСЏ.
    РџРµСЂРµС…РѕРїР»СЋС” РЅР°Р№С‚РёРїРѕРІС–С€С– РІРёРЅСЏС‚РєРё С– РїРѕРІРµСЂС‚Р°С” Р·СЂРѕР·СѓРјС–Р»Рµ РїРѕРІС–РґРѕРјР»РµРЅРЅСЏ.
    """

    @wraps(func)
    def inner(*args: Any, **kwargs: Any) -> str:
        try:
            return func(*args, **kwargs)
        except ValueError as error:
            return str(error)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter the required arguments for the command."

    return inner  # type: ignore[return-value]


def parse_input(user_input: str) -> tuple[str, list[str]]:
    """
    Р РѕР·Р±РёСЂР°С” РІРІРµРґРµРЅРёР№ СЂСЏРґРѕРє РЅР° РєРѕРјР°РЅРґСѓ С‚Р° Р°СЂРіСѓРјРµРЅС‚Рё.
    РџСЂРёРєР»Р°Рґ: "add John 0501234567" -> ("add", ["John", "0501234567"])
    """
    parts = user_input.strip().split()
    if not parts:
        return "", []
    command, *args = parts
    return command.lower(), args


@input_error
def add_contact(args: list[str], book: AddressBook) -> str:
    """
    add [С–Рј'СЏ] [С‚РµР»РµС„РѕРЅ]
    Р”РѕРґР°С” РЅРѕРІРёР№ РєРѕРЅС‚Р°РєС‚ Р°Р±Рѕ РґРѕРґР°С” С‚РµР»РµС„РѕРЅ РґРѕ С–СЃРЅСѓСЋС‡РѕРіРѕ.
    """
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args: list[str], book: AddressBook) -> str:
    """
    change [С–Рј'СЏ] [СЃС‚Р°СЂРёР№ С‚РµР»РµС„РѕРЅ] [РЅРѕРІРёР№ С‚РµР»РµС„РѕРЅ]
    Р—Р°РјС–РЅСЋС” С‚РµР»РµС„РѕРЅ Сѓ РєРѕРЅС‚Р°РєС‚С–.
    """
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args: list[str], book: AddressBook) -> str:
    """
    phone [С–Рј'СЏ]
    РџРѕРІРµСЂС‚Р°С” С‚РµР»РµС„РѕРЅРё РєРѕРЅС‚Р°РєС‚Сѓ (С‡РµСЂРµР· '; ').
    """
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    if not record.phones:
        return "No phone numbers found for this contact."
    return "; ".join(phone.value for phone in record.phones)


def show_all(book: AddressBook) -> str:
    """
    all
    Р’РёРІРѕРґРёС‚СЊ РІСЃС– РєРѕРЅС‚Р°РєС‚Рё (РєРѕР¶РµРЅ Record СЏРє РѕРєСЂРµРјРёР№ СЂСЏРґРѕРє).
    """
    if not book.data:
        return "Address book is empty."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args: list[str], book: AddressBook) -> str:
    """
    add-birthday [С–Рј'СЏ] [РґР°С‚Р° DD.MM.YYYY]
    Р”РѕРґР°С” (Р°Р±Рѕ РѕРЅРѕРІР»СЋС”) РґРµРЅСЊ РЅР°СЂРѕРґР¶РµРЅРЅСЏ РґР»СЏ РєРѕРЅС‚Р°РєС‚Сѓ.
    """
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args: list[str], book: AddressBook) -> str:
    """
    show-birthday [С–Рј'СЏ]
    РџРѕРєР°Р·СѓС” РґРµРЅСЊ РЅР°СЂРѕРґР¶РµРЅРЅСЏ РєРѕРЅС‚Р°РєС‚Сѓ.
    """
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    if record.birthday is None:
        return "Birthday is not set for this contact."
    return str(record.birthday)


@input_error
def birthdays(_: list[str], book: AddressBook) -> str:
    """
    birthdays
    РџРѕРєР°Р·СѓС” РґРЅС– РЅР°СЂРѕРґР¶РµРЅРЅСЏ РЅР° РЅР°СЃС‚СѓРїРЅРёР№ С‚РёР¶РґРµРЅСЊ.
    """
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next week."
    return "\n".join(f"{item['name']}: {item['congratulation_date']}" for item in upcoming)


def save_data(book: AddressBook, filename: str = DATA_FILE) -> None:
    """Зберігає адресну книгу у файл за допомогою pickle."""
    with open(filename, "wb") as file:
        pickle.dump(book, file)


def load_data(filename: str = DATA_FILE) -> AddressBook:
    """Завантажує адресну книгу з файла або повертає нову, якщо файл недоступний."""
    try:
        with open(filename, "rb") as file:
            data: Any = pickle.load(file)
            if isinstance(data, AddressBook):
                return data
    except FileNotFoundError:
        pass
    except (pickle.PickleError, EOFError, AttributeError):
        pass
    return AddressBook()

def main() -> None:
    """
    Р“РѕР»РѕРІРЅРёР№ С†РёРєР» РїСЂРѕРіСЂР°РјРё: С‡РёС‚Р°С” РєРѕРјР°РЅРґРё РєРѕСЂРёСЃС‚СѓРІР°С‡Р° С– РІРёРєР»РёРєР°С” РІС–РґРїРѕРІС–РґРЅС– РѕР±СЂРѕР±РЅРёРєРё.
    """
    book: AddressBook = load_data()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ").strip()
        command, args = parse_input(user_input)

        if not command:
            print("Invalid command.")
        elif command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()










