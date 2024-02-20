import tkinter as tk
from tkinter import filedialog
import serial.tools.list_ports
import serial
import math
import asyncio
import threading

def get_usb_port():
    for port in serial.tools.list_ports.comports():
        if 'COM5' in port.description: 
            return port.device
    return None

def open_serial_port(baudrate=9600):
    try:
        port = get_usb_port()
        if port:
            ser = serial.Serial(port, baudrate)
            return ser
        else:
            print("Error: USB port not found.")
            return None
    except Exception as e:
        print(f"Error opening the serial port: {e}")
        return None
    
async def flash_firmware(file_label_text, baudrate, progress_label):
    file_prefix = "Selected File: "
    if not file_label_text.startswith(file_prefix):
        print("Invalid file label format.")
        return
    
    file_path = file_label_text[len(file_prefix):]  # Extract file path
    if not file_path:
        print("Please select a file.")
        return

    print("File path:", file_path)  # Debugging print statement

    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return
    except Exception as e:
        print(f"Error opening file: {e}")
        return

    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return

    total_frames = math.ceil(len(file_data) / 7)
    frame_num = 1  # Initialize frame_num
    for _ in range(total_frames):
        start_index = (frame_num - 1) * 7
        end_index = min(frame_num * 7, len(file_data))
        payload = file_data[start_index:end_index]
        checksum = sum(payload) & 0xFF
        payload += bytes([checksum])

        try:
            transfer_data_payload(ser, 68, 3, frame_num, *payload)
            
            # Increment frame_num and handle rollback
            frame_num += 1
            if frame_num > 255:
                frame_num = 1

            # Calculate percentage based on total_frames and current frame_num
            percentage = ((frame_num - 1) / total_frames) * 100
            progress_label.config(text=f"Progress: {percentage:.2f}%")
        except serial.SerialException as e:
            print(f"Error writing to serial port: {e}")
            break
    
    print("Firmware flashing completed.")
    ser.close()


# async def flash_firmware(file_label_text, baudrate, progress_label):
#     file_prefix = "Selected File: "
#     if not file_label_text.startswith(file_prefix):
#         print("Invalid file label format.")
#         return
    
#     file_path = file_label_text[len(file_prefix):]  # Extract file path
#     if not file_path:
#         print("Please select a file.")
#         return

#     print("File path:", file_path)  # Debugging print statement

#     try:
#         with open(file_path, "rb") as f:
#             file_data = f.read()
#     except FileNotFoundError:
#         print(f"File not found: {file_path}")
#         return
#     except Exception as e:
#         print(f"Error opening file: {e}")
#         return

#     ser = open_serial_port(baudrate)
#     if not ser:
#         print("Serial port not available.")
#         return

#     total_frames = math.ceil(len(file_data) / 7)
#     for frame_num in range(1, total_frames + 1):
#         start_index = (frame_num - 1) * 7
#         end_index = min(frame_num * 7, len(file_data))
#         payload = file_data[start_index:end_index]
#         checksum = sum(payload) & 0xFF
#         payload += bytes([checksum])

#         try:
#             transfer_data_payload(ser, 68, 3, frame_num, *payload)
#             frame_num = (frame_num % 255) + 1

#             # ser.write(payload)
#             percentage = (frame_num / total_frames) * 100
#             progress_label.config(text=f"Progress: {percentage:.2f}%")
#         except serial.SerialException as e:
#             print(f"Error writing to serial port: {e}")
#             break
    
#     print("Firmware flashing completed.")
#     ser.close()
    
def transfer_data_payload(ser, main_id, sequence_id, frame_num, *payload_bytes):
    payload = bytearray([main_id, sequence_id, frame_num]) + bytearray(payload_bytes)
    print(payload)
    ser.write(payload)
    print(f"Transferred Data: {payload}")

def import_file(file_label):
    file_path = filedialog.askopenfilename()
    if file_path:
        file_label.config(text="Selected File: " + file_path)
    else:
        print("No file selected.")
    return file_path

def flash_firmware_thread(file_label_text, baudrate, progress_label):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(flash_firmware(file_label_text, baudrate, progress_label))
    loop.close()

def main():
    window = tk.Tk()
    window.title("Bootloader")
    window.geometry("400x400")
    
    main_container = tk.Frame(window)

    nav_frame = tk.Frame(main_container)
    nav_label = tk.Label(nav_frame, text="BootLoader Flashing", foreground="white", background="black", width=100)
    nav_label.pack(fill=tk.BOTH, expand=True)

    container_frame = tk.Frame(main_container)
    file_label = tk.Label(container_frame, text="", foreground="black", background="white")
    file_label.pack()
    button_import = tk.Button(container_frame, text="Import File", width=25, height=5, bg="blue", fg="yellow", command=lambda: import_file(file_label))
    button_import.pack(pady=10)
    progress_label = tk.Label(container_frame, text="Progress: 0.00%", foreground="black", background="white")
    progress_label.pack()
    flash_button = tk.Button(window, text="Flash Firmware", command=lambda: threading.Thread(target=flash_firmware_thread, args=(file_label.cget("text"), 9600, progress_label)).start())
    flash_button.pack()
    
    footer_frame = tk.Frame(main_container)
    footer_label = tk.Label(footer_frame, text="EMotorad", foreground="white", background="green", width=100)
    footer_label.pack(fill=tk.BOTH, expand=True)

    nav_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    container_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    footer_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    main_container.pack(fill=tk.BOTH, expand=True)

    window.mainloop()

if __name__ == "__main__":
    main()
