import tkinter as tk
from tkinter import filedialog
import serial.tools.list_ports
import serial
import math
import asyncio
import threading
import time

def get_usb_port():
    for port in serial.tools.list_ports.comports():
        if 'COM5' in port.description: 
            return port.device
    return None

baudrate=9600



def upload_file(file_label_text,baudrate=9600):
    print(baudrate)
    file_prefix = "Selected File: "
    if not file_label_text.startswith(file_prefix):
        print("Invalid file label format.")
        return
    
    file_path = file_label_text[len(file_prefix):]
    if not file_path:
        print("Please select a file.")
        return

    print("File path:", file_path)

    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return
    except Exception as e:
        print(f"Error opening file: {e}")
        return
    return file_data 


def import_file(file_label):
    return lambda: upload_file(file_label)

def open_serial_port(baudrate):
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

    total_frames = math.ceil(len(file_data) / 8)
    

    arr_start = []
    arr_end = []
    arr_payload_data  = []
    arr_sum_payload = []
    arr_cal_check = []
    arr_payload_checksum = []
    
    frame_num = 1
    for _ in range(total_frames):
        start_index = (frame_num - 1) * 8
        # print(start_index)
        # arr_start.append(start_index)
        end_index = min(frame_num * 8, len(file_data))
        # print(end_index)
        # arr_end.append(end_index)
        payload = file_data[start_index:end_index]
        # arr_payload_data.append(payload)
        # arr_cal_check.append(checksum)
        payload = bytes(payload)
        print(payload)
        # arr_payload_data.append(payload)

        try:
            send_payload(ser, 68, 3, frame_num, *payload)
            time.sleep(0.02) 
            
            # Increment frame_num and handle rollback
            frame_num += 1
            if frame_num >= 255:
                frame_num = 1

            # Calculate percentage based on total_frames and current frame_num
            percentage = ((frame_num - 1) / total_frames) * 100
            progress_label.config(text=f"Progress: {percentage:.2f}%")
            # print(arr_start[:11])
            # print("---------------------------------------------------------------------")
            
            # print(arr_end[total_frames-start_index:total_frames])
            # print("---------------------------------------------------------------------")
            
            # print(payload[:7])
            # print("---------------------------------------------------------------------")
            
            # print(arr_payload_data)
            # print("---------------------------------------------------------------------")
            
            # print(arr_sum_payload)
            # print("---------------------------------------------------------------------")
            # print(arr_cal_check)
            # print("---------------------------------------------------------------------")
            # print(arr_payload_checksum)
            # print("---------------------------------------------------------------------")
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
    before_check_sum = [main_id, sequence_id, *payload_bytes]
    print(before_check_sum)
    
    checksum = cal_checksum(*before_check_sum)
    print(checksum)
    payload = before_check_sum + [checksum] 
    print(payload)
    ser.write(payload)
    print(ser, main_id, sequence_id, *payload_bytes)
    print(f"ECU Reset Payload: {payload}")

def reset_firmware():
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    try:
        send_payload(ser, 68, 6, 90, 90, 90, 90, 90, 90, 90, 90, 90)
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    print("Firmware reset completed.")
    ser.close()

def ecu_reset_payload(ser, main_id, sequence_id, *payload_bytes):
    before_check_sum = [main_id, sequence_id, *payload_bytes]
    print(before_check_sum)
    
    checksum = cal_checksum(*before_check_sum)
    print(checksum)
    payload = before_check_sum + [checksum] 
    print(payload)
    ser.write(payload)
    print(ser, main_id, sequence_id, *payload_bytes)
    print(f"ECU Reset Payload: {payload}")



def calculate_program_size(file_label_text):

    file = upload_file(file_label_text)
    
    program_size = len(file)
    return program_size

def total_frame(file_label_text):
    size = calculate_program_size(file_label_text)
    total_frames = math.ceil(size / 8)
    return total_frame

    
    
def break_down_program_size(file_label_text):
    program_size = calculate_program_size(file_label_text)
    size_byte_1 = program_size & 0xFF
    size_byte_2 = (program_size >> 8) & 0xFF
    size_byte_3 = (program_size >> 16) & 0xFF
    size_byte_4 = (program_size >> 24) & 0xFF
    return size_byte_1, size_byte_2, size_byte_3, size_byte_4
    
 

def cal_checksum(*payload_bytes):
    print(*payload_bytes)
    checksum = payload_bytes[0]
    for byte in payload_bytes[1:]:  
        checksum ^= byte
    print(checksum)
    return checksum

    
# def send_program_size_payload(ser,main_id,sequence_id,*payload_bytes):
#     payload = bytearray([main_id, sequence_id]) + bytearray(payload_bytes)
#     checksum = cal_checksum(bytearray([main_id, sequence_id]) + bytearray(payload_bytes))
#     payload += bytes([checksum])
#     ser.write(payload)
#     print(f"Program Size Payload: {payload}")
    
def program_size(file_label):
    file_data = upload_file(file_label)
    if file_data:
        size_byte_1, size_byte_2, size_byte_3, size_byte_4 = break_down_program_size(file_label)
        ser = open_serial_port(baudrate)
        
        if not ser:
            print("Serial port not available.")
            return
        if ser:
            try:
                send_payload(ser, 68, 2, size_byte_1, size_byte_2, size_byte_3, size_byte_4, 0x5A, 0x5A, 0x5A, 0x5A)
            except serial.SerialException as e:
                print(f"Error writing to serial port: {e}")
            finally:
                ser.close()
    print("Program Size command sent.")
        
    

def erase_memory():
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    try:
        send_payload(ser, 68, 1, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A)
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    print("Memory erase command sent.")
    ser.close()

# def erase_memory_payload(ser, main_id, sequence_id, *payload_bytes):
#     payload = bytearray([main_id, sequence_id]) + bytearray(payload_bytes)
#     checksum = bytearray([main_id, sequence_id]) + bytearray(payload_bytes)
#     print(checksum)
#     payload += bytes([checksum])
#     ser.write(payload)
#     print(f"Checksum Payload: {payload}")
#     print(ser, main_id, sequence_id, *payload_bytes)
#     print(f"Erase Memory Payload: {payload}")
    


    
    
def send_checksum_payload(ser, main_id, sequence_id, *payload_bytes):
    before_check_sum = [main_id, sequence_id, *payload_bytes]
    print(before_check_sum)
    
    checksum = cal_checksum(*before_check_sum)
    print(checksum)
    payload = before_check_sum + [checksum] 
    print(payload)
    ser.write(payload)
    print(ser, main_id, sequence_id, *payload_bytes)
    print(f"ECU Reset Payload: {payload}")
    
    
def checksum_payload():
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    try:
        send_checksum_payload(ser, 68, 4, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A)
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    print("Checksum payload sent.")
    ser.close()

def send_payload(ser, main_id, sequence_id, *payload_bytes):
    before_check_sum = [main_id, sequence_id, *payload_bytes]
    print(before_check_sum)
    
    checksum = cal_checksum(*before_check_sum)
    print(checksum)
    payload = before_check_sum + [checksum] 
    print(payload)
    ser.write(payload)
    print(ser, main_id, sequence_id, *payload_bytes)
    print(f"ECU Reset Payload: {payload}")
    
    
def application_flashed_properly_payload():
    ser = open_serial_port(baudrate)
    
    if not ser:
        print("Serial port not available.")
        return
    
    try:
        send_payload(ser, 68, 7, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A, 0x5A)
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    finally:
        ser.close()

    print("Application Flashed Properly Payload sent.")      
    

def display():
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    try:
        send_payload(ser, 1, 20, 0x9A, 0x9A, 0x9A, 0x9A, 0x9A, 0x9A, 0x9A, 0x9A,  0x9A, 0x9A, 0x9A, 0x9A, 0x9A, 0x9A, 0x9A, 0x9A, 0x9A)
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    print("Display  payload command sent.")
    ser.close()

# def display_payload(ser, main_id, sequence_id, *payload_bytes):
#     payload = bytearray([main_id, sequence_id]) + bytearray(payload_bytes)
#     ser.write(payload)
#     print(f"Display Data: {payload}")



# def erase_memory_payload(ser, main_id, sequence_id, *payload_bytes, checksum):
    
#     print("Erase Memory Payload(10 bytes):")
#     print(f"Main ID: {main_id}")
#     print(f"Sequence ID: {sequence_id}")
#     print("Payload Bytes:")
#     print(f"Checksum: {checksum}")

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
    
    reset_button = tk.Button(window, text="Reset Firmware", command=reset_firmware)
    reset_button.pack()
    
    erase_button = tk.Button(window, text="Erase Memory", command=erase_memory)
    erase_button.pack()
    
    program_size_button = tk.Button(window, text="Program Size", command=lambda: threading.Thread(target=program_size, args=(file_label.cget("text"),)).start())
    program_size_button.pack()
    
    checksum_button = tk.Button(window, text="Checksum Payload", command=checksum_payload)
    checksum_button.pack()
    
    app_flashed_button = tk.Button(window, text="Application Flashed Properly", command=application_flashed_properly_payload)
    app_flashed_button.pack()
    
    
    display_button = tk.Button(window, text="Display Flashed Properly", command=display)
    display_button.pack()
    
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