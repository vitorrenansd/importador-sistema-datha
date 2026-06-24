import tkinter as tk
from controller.app_controller import AppController


def main():
    root = tk.Tk()
    controller = AppController(root)
    root.mainloop()


if __name__ == "__main__":
    main()
