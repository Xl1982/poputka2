from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

seats_markup = InlineKeyboardMarkup(row_width=5)
seats_buttons = [
    InlineKeyboardButton(text=str(num), callback_data=f"seats:{num}") for num in range(1,5)
]

cancel_button = InlineKeyboardButton("Отмена", callback_data="cancel")
seats_buttons.append(cancel_button)
seats_markup.add(*seats_buttons)
