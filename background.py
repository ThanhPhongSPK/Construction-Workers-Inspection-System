import tkinter as tk
from PIL import Image, ImageTk
import subprocess
import UI


class WarningSystemUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Final Term Project")
        self.geometry("1920x1080")
        self.configure(bg="white")  # Set background full white
        self.create_widgets()

    def create_widgets(self):
        # Content frame
        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.place(relwidth=0.9, relheight=0.9, relx=0.05, rely=0.05)

        # Header
        header_frame = tk.Frame(self.content_frame, bg="white")
        header_frame.pack(fill=tk.X, pady=5)

        # Logo left
        logo_left = Image.open("ute_logo.png")  # Update the path to your logo image
        logo_left = logo_left.resize((145, 150), Image.LANCZOS)
        logo_image_left = ImageTk.PhotoImage(logo_left)
        logo_label_left = tk.Label(header_frame, image=logo_image_left, bg="white")
        logo_label_left.image = logo_image_left
        logo_label_left.pack(side=tk.LEFT, padx=0, pady=10)

        # University name header
        header_title = ("HO CHI MINH CITY UNIVERSITY OF"
                        "\nTECHNOLOGY AND EDUCATION")
        header_title_label = tk.Label(header_frame, text=header_title, bg="white", font=("Lato", 18, "bold"))
        header_title_label.pack(side=tk.LEFT, padx=10)  # Adjusted padding

        # Right frame for logo faculty text
        right_frame = tk.Frame(header_frame, bg="white")
        right_frame.pack(side=tk.RIGHT, padx=10)

        logo_right = Image.open("CKM logo.png")  # Update the path to your logo image
        logo_right = logo_right.resize((145, 138), Image.LANCZOS)
        logo_image_right = ImageTk.PhotoImage(logo_right)
        logo_label_right = tk.Label(right_frame, image=logo_image_right, bg="white")
        logo_label_right.image = logo_image_right
        logo_label_right.pack(side=tk.LEFT, padx=5)

        faculty_label = tk.Label(right_frame, text="FACULTY OF MECHANICAL ENGINEERING", bg="white",
                                 font=("Lato", 18, "bold"))
        faculty_label.pack(side=tk.LEFT, padx=10)

        # Name project frame
        self.name_project_frame = tk.Frame(self, bg="white")
        self.name_project_frame.place(relwidth=0.43, relheight=0.3, relx=0.1, rely=0.35)
        # Main project title and subtitle
        main_title_frame = tk.Frame(self.name_project_frame, bg="white")
        main_title_frame.pack(fill=tk.X, pady=0)

        main_title_text = (
            "Major: Robot & AI         Subject: Machine Vision\n"
        )
        main_title_label = tk.Label(main_title_frame, text=main_title_text, bg="white", font=("Lato", 18, "bold"))
        main_title_label.pack()

        name_project_label = tk.Label(main_title_frame, text="Final Term Project\n"
                                                             "DETECT CONSTRUCTION WORKER", bg="white",
                                      font=("Lato", 20, "bold"))
        name_project_label.pack(anchor=tk.CENTER, pady=0)

        # Instructor and Performers
        details_frame = tk.Frame(self, bg="light gray")
        details_frame.place(relwidth=0.4, relheight=0.23, relx=0.1155, rely=0.54)

        details_inner_frame = tk.Frame(details_frame, bg="light gray")
        details_inner_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        instructor_label = tk.Label(details_inner_frame, text="INSTRUCTOR: Ph.D Nguyen Van Thai", bg="light gray",
                                    font=("Lato", 18))
        instructor_label.grid(row=0, columnspan=2, pady=5)

        performers_title = tk.Label(details_inner_frame, text="PERFORMER:", bg="light gray",
                                    font=("Lato", 18))
        performers_title.grid(row=1, column=0, sticky=tk.W, padx=10)
        id_title = tk.Label(details_inner_frame, text="ID:", bg="light gray", font=("Lato", 18))
        id_title.grid(row=1, column=1, sticky=tk.W, padx=10)

        performers = [
            ("Dinh Duc Duy", "22134001"),
            ("Le Quoc Thinh", "21134013"),
            ("Huynh Thanh Phong", "21134009")
        ]

        for i, (name, id) in enumerate(performers):
            name_label = tk.Label(details_inner_frame, text=name, bg="light gray", font=("Lato", 16))
            name_label.grid(row=i + 2, column=0, sticky=tk.W, padx=10)
            id_label = tk.Label(details_inner_frame, text=id, bg="light gray", font=("Lato", 16))
            id_label.grid(row=i + 2, column=1, sticky=tk.W, padx=10)

        # Image display
        image_frame = tk.Frame(self.content_frame, bg="white")
        image_frame.pack(pady=20, fill=tk.X)  # Allow image frame to fill horizontally

        face_image = Image.open("construction_worker.jpg")  # Use the uploaded face image
        face_image = face_image.resize((500, 500), Image.LANCZOS)
        face_image_tk = ImageTk.PhotoImage(face_image)
        face_image_label = tk.Label(image_frame, image=face_image_tk, bg="white")
        face_image_label.image = face_image_tk
        face_image_label.pack(side=tk.RIGHT, padx=100, pady=10)  # Pack the image to the right

        # Start button
        start_button = tk.Button(self.content_frame, text="START", command=self.start_button_clicked, width=20,
                                 height=5, bg='green', fg='white', font=("Lato", 15,))
        start_button.pack(side=tk.BOTTOM, padx=50, pady=0)

    def start_button_clicked(self):
        self.destroy()  # Đóng cửa sổ hiện tại
        subprocess.run(["python3", "UI.py"])


if __name__ == "__main__":
    app = WarningSystemUI()
    app.mainloop()
