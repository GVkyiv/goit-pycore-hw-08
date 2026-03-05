from __future__ import annotations

from collections import UserDict
from datetime import date, datetime, timedelta
from functools import wraps
import pickle
from typing import Any, Callable, TypeVar

# Узагальнений тип для декоратора: приймає функцію, що повертає str
T = TypeVar("T", bound=Callable[..., str])
DATA_FILE = "addressbook.pkl"


class Field:
    """
    Базовий клас для всіх полів (Name, Phone, Birthday тощо).
    Зберігає значення та дозволяє гарно виводити його як рядок.
    """
    value: Any

    def __init__(self, value: Any) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    """Поле для зберігання імені контакту."""
    pass


class Phone(Field):
    """
    Поле для зберігання телефону.
    Валідація: телефон має бути рядком з рівно 10 цифр.
    """

    def __init__(self, value: str) -> None:
        if not isinstance(value, str) or not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    """
    Поле для дати народження.
    Валідація: формат DD.MM.YYYY.
    Усередині зберігаємо не рядок, а об’єкт date (зручніше для розрахунків).
    """

    def __init__(self, value: str) -> None:
        try:
            parsed_date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError as error:
            # Піднімаємо "людську" помилку з правильним повідомленням
            raise ValueError("Invalid date format. Use DD.MM.YYYY") from error
        super().__init__(parsed_date)

    def __str__(self) -> str:
        # При виведенні назад показуємо як DD.MM.YYYY
        return self.value.strftime("%d.%m.%Y")


class Record:
    """
    Запис адресної книги: ім'я, список телефонів, (опційно) день народження.
    """

    def __init__(self, name: str) -> None:
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday | None = None

    def add_phone(self, phone: str) -> None:
        # Додаємо телефон, при створенні Phone відбудеться валідація
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> None:
        # Видаляємо телефон, якщо його не знайдено — помилка
        phone_to_remove = self.find_phone(phone)
        if phone_to_remove is None:
            raise ValueError("Phone number not found.")
        self.phones.remove(phone_to_remove)

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        # Знаходимо старий телефон і замінюємо його значенням нового
        phone_to_edit = self.find_phone(old_phone)
        if phone_to_edit is None:
            raise ValueError("Phone number not found.")
        # Важливо: новий номер також перевіряється через Phone(...)
        phone_to_edit.value = Phone(new_phone).value

    def find_phone(self, phone: str) -> Phone | None:
        # Повертаємо об'єкт Phone, якщо знайдено, або None
        for saved_phone in self.phones:
            if saved_phone.value == phone:
                return saved_phone
        return None

    def add_birthday(self, birthday: str) -> None:
        # Додаємо/оновлюємо день народження (валідність перевіряє Birthday)
        self.birthday = Birthday(birthday)

    def __str__(self) -> str:
        # Формуємо зручний рядок для виводу запису
        phones = "; ".join(phone.value for phone in self.phones) or "no phones"
        birthday = str(self.birthday) if self.birthday else "not set"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"


class AddressBook(UserDict):
    """
    Адресна книга — це словник (name -> Record).
    Наслідуємось від UserDict, щоб мати стандартну поведінку словника.
    """

    data: dict[str, Record]

    def add_record(self, record: Record) -> None:
        # Додаємо запис у словник за ключем імені
        self.data[record.name.value] = record

    def find(self, name: str) -> Record | None:
        # Шукаємо запис за ім’ям. Якщо нема — None
        return self.data.get(name)

    def delete(self, name: str) -> None:
        # Видаляємо запис за ім’ям, якщо він існує
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
        Повертає список людей, яких треба привітати протягом наступних 7 днів.
        Якщо день народження припадає на вихідні (Сб/Нд),
        дата привітання переноситься на найближчий понеділок.
        """
        today = date.today()
        upcoming_birthdays: list[dict[str, str]] = []

        for record in self.data.values():
            # Пропускаємо контакти без дня народження
            if record.birthday is None:
                continue

            # День народження цього року (тільки день/місяць, рік = поточний)
            birthday_this_year = self._get_birthday_for_year(record.birthday.value, today.year)

            # Якщо вже минув у цьому році — беремо наступний рік
            if birthday_this_year < today:
                birthday_this_year = self._get_birthday_for_year(
                    record.birthday.value, today.year + 1
                )

            # Скільки днів залишилось до ДН
            days_until_birthday = (birthday_this_year - today).days

            # Беремо тільки наступний тиждень (0..7)
            if days_until_birthday > 7:
                continue

            # Дата привітання: за замовчуванням сама дата ДН
            congratulation_date = birthday_this_year

            # Якщо це субота (5) або неділя (6) — переносимо на понеділок
            if congratulation_date.weekday() >= 5:
                congratulation_date += timedelta(days=7 - congratulation_date.weekday())

            upcoming_birthdays.append(
                {
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime("%d.%m.%Y"),
                }
            )

        # Сортуємо за датою привітання
        return sorted(
            upcoming_birthdays,
            key=lambda item: datetime.strptime(item["congratulation_date"], "%d.%m.%Y"),
        )


def input_error(func: T) -> T:
    """
    Декоратор для обробки помилок введення.
    Перехоплює найтиповіші винятки і повертає зрозуміле повідомлення.
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
    Розбирає введений рядок на команду та аргументи.
    Приклад: "add John 0501234567" -> ("add", ["John", "0501234567"])
    """
    parts = user_input.strip().split()
    if not parts:
        return "", []
    command, *args = parts
    return command.lower(), args


@input_error
def add_contact(args: list[str], book: AddressBook) -> str:
    """
    add [ім'я] [телефон]
    Додає новий контакт або додає телефон до існуючого.
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
    change [ім'я] [старий телефон] [новий телефон]
    Замінює телефон у контакті.
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
    phone [ім'я]
    Повертає телефони контакту (через '; ').
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
    Виводить всі контакти (кожен Record як окремий рядок).
    """
    if not book.data:
        return "Address book is empty."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args: list[str], book: AddressBook) -> str:
    """
    add-birthday [ім'я] [дата DD.MM.YYYY]
    Додає (або оновлює) день народження для контакту.
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
    show-birthday [ім'я]
    Показує день народження контакту.
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
    Показує дні народження на наступний тиждень.
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
    Головний цикл програми: читає команди користувача і викликає відповідні обробники.
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











