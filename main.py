import tkinter as tk
from utils import execute_python_code

execute_python_code('print("hello")')

def send_message():
    message = input_entry.get()  # Получение текста из поля ввода
    output_text.insert(tk.END, message + "\n")  # Добавление текста в блок после нажатия на кнопку

window = tk.Tk()

# Блок с текстом
label = tk.Label(window, text="Введите сообщение:")
label.pack()

# Поле ввода
input_entry = tk.Entry(window)
input_entry.pack()

# Кнопка "Отправить"
send_button = tk.Button(window, text="Отправить", command=send_message)
send_button.pack()

# Блок с текстом после нажатия на кнопку
output_text = tk.Text(window)
output_text.pack()

window.mainloop()
