import os


def change_str(str1: str, str2: str) -> None:
    """Проходим по всем файлам и каталогам в указанной директории и заменяет str1 на str2"""
    directory_path = os.path.dirname(__file__)
    for dirpath, dirnames, filenames in os.walk(directory_path):
        if '.venv' in dirpath:
            continue
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if filename == 'change_string.py':
                continue
            if os.path.isfile(file_path):  # Проверка, что это файл
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:  # Открытие файла
                        text = file.read()
                    if str1 in text:  # Проверка, содержит ли файл str1
                        new_text = text.replace(str1, str2)
                        with open(file_path, 'w', encoding='utf-8') as file:  # Записываем изменения обратно в файл
                            file.write(new_text)
                            print(f"Заменено в файле: {file_path}")
                except Exception as e:
                    print(f"Не удалось обработать файл {file_path}: {e}")


if __name__ == '__main__':
    change_str('Orders', 'Positions')
