import tkinter as tk
from tkinter import filedialog
import serial.tools.list_ports
import serial
import math
import threading
import time

baudrate = 9600

def get_usb_port():
    for port in serial.tools.list_ports.comports():
        if 'COM5' in port.description: 
            return port.device
    return None

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

def listen_inputs(callback):
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    
    try:
        while True:
            if ser.in_waiting > 0:
                incoming_data = ser.read(ser.in_waiting)
                callback(incoming_data)
            time.sleep(0.1)  # Add a small delay to avoid high CPU usage in the loop
    finally:
        ser.close()  # Close the serial port when done

def process_feedback(data):
    if len(data) != 8:
        print("Invalid feedback payload length")
        return

    feedback_id = data[1]
    d1 = data[2]
    d2 = data[3]
    d3 = data[4]
    d4 = data[5]
    checksum = data[6]

    calculated_checksum = sum(data[1:6]) & 0xFF  # Calculate checksum using XOR
    if calculated_checksum != checksum:
        print("Checksum mismatch")
        return

    feedback_messages = {
        1: "Erased Successful",
        2: "Erase Failure",
        3: f"Frame Received (Requested Frame Number: {d1})",
        4: "Frame Receive Failure",
        5: f"Checksum Data (Checksum Value: {d1}{d2}{d3}{d4})",
        6: f"Program Size Received ({d1} bytes)",
        7: "Flashed Status Received",
        8: "App Sign failure"
    }

    if feedback_id in feedback_messages:
        feedback_message = feedback_messages[feedback_id]
        print(f"Feedback ID: {feedback_id} - {feedback_message}")
    else:
        print(f"Unknown Feedback ID: {feedback_id}")


def listenUltraProxMax():
    listen_inputs(process_feedback)

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
    
    feedback_button = tk.Button(window, text="Listen for Feedback", command=listenUltraProxMax)
    feedback_button.pack()
    
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





    
    

# async def flash_firmware(file_label_text, baudrate, progress_label):
#     # Check file label format
#     file_prefix = "Selected File: "
#     if not file_label_text.startswith(file_prefix):
#         print("Invalid file label format.")
#         return
    
#     # Extract file path
#     file_path = file_label_text[len(file_prefix):]
#     if not file_path:
#         print("Please select a file.")
#         return

#     print(f"File path: {file_path}")  # Debugging print statement

#     try:
#         # Read file data
#         with open(file_path, "rb") as f:
#             file_data = f.read()
#     except FileNotFoundError:
#         print(f"File not found: {file_path}")
#         return
#     except Exception as e:
#         print(f"Error opening file: {e}")
#         return

#     # Open serial port
#     ser = open_serial_port(baudrate)
#     if not ser:
#         print("Serial port not available.")
#         return

#     total_frames = math.ceil(len(file_data) / 8)
    
#     frame_num = 1
#     for _ in range(total_frames):
#         start_index = (frame_num - 1) * 8
#         print(f"Start index {start_index}")

#         end_index = min(frame_num * 8, len(file_data))
#         print(f"end Index {end_index}")
#         payload = file_data[start_index:end_index]
#         print(f"before bytes payload meaning vanilla payload {payload}")
#         payload = bytes(payload)
#         print(f"Length of the payload {len(payload)}")
#         print(f"after bytes payload {payload}")
#         print(f"initial frame number {frame_num}")

#         try:
#             print(*payload)
#             payload_values = ' '.join(str(byte) for byte in payload)
#             print(f"{ser} 68 3 {frame_num} {payload_values}")
#             send_payload(ser, 68, 3, frame_num, *payload)
#             frame_num += 1
#             t = time.localtime()
#             current_time = time.strftime("%H:%M:%S", t)
#             print(current_time)
#             # Delay for 50 ms after the first payload is sent
#             await asyncio.sleep(0.05)
#             t = time.localtime()
#             current_time = time.strftime("%H:%M:%S", t)
#             print(current_time)
#             print("after")
            
#             # Calculate percentage based on total_frames and current frame_num
#             percentage = ((frame_num - 1) / total_frames) * 100
#             progress_label.config(text=f"Progress: {percentage:.2f}%")
            
#         except serial.SerialException as e:
#             print(f"Error writing to serial port: {e}")
#             break

#     print("Firmware flashing completed.")
#     ser.close()







    
# async def flash_firmware(file_label_text, baudrate, progress_label):
#     # Check file label format
#     file_prefix = "Selected File: "
#     if not file_label_text.startswith(file_prefix):
#         print("Invalid file label format.")
#         return
    
#     # Extract file path
#     file_path = file_label_text[len(file_prefix):]
#     if not file_path:
#         print("Please select a file.")
#         return

#     print("File path:", file_path)  # Debugging print statement

#     try:
#         # Read file data
#         with open(file_path, "rb") as f:
#             file_data = f.read()
#     except FileNotFoundError:
#         print(f"File not found: {file_path}")
#         return
#     except Exception as e:
#         print(f"Error opening file: {e}")
#         return

#     # Open serial port
#     ser = open_serial_port(baudrate)
#     if not ser:
#         print("Serial port not available.")
#         return

#     print(f"vanilla length of file:" + (len(file_data) / 8))
#     total_frames = math.ceil(len(file_data) / 8)
#     print("After ceiling to the next number " + total_frame)
    
#     # Loop through frames and send data
#     frame_num = 1
#     for _ in range(total_frames):
#         start_index = (frame_num - 1) * 7
#         print("Start index " + end_index)

#         end_index = min(frame_num * 7, len(file_data))
#         print("end Index " + end_index)
#         payload = file_data[start_index:end_index]
#         print("before bytes payload meaning vanilla payload " + payload)
#         payload = bytes(payload)
#         print("Length of the payload " + len(payload))
#         print("after bytes payload " + payload)
#         print("initial fram number " + frame_num)

#         try:
#             print(ser, 68, 3, frame_num, *payload)
#             send_payload(ser, 68, 3, frame_num, *payload)
#             frame_num += 1
#             print("after first frame " + frame_num)
#             # Delay for 50 ms
#             time.sleep(5000)

#             # Calculate percentage based on total_frames and current frame_num
#             percentage = ((frame_num - 1) / total_frames) * 100
#             progress_label.config(text=f"Progress: {percentage:.2f}%")
            
#         except serial.SerialException as e:
#             print(f"Error writing to serial port: {e}")
#             break

#     print("Firmware flashing completed.")
#     ser.close()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
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

#     total_frames = math.ceil(len(file_data) / 8)
    

#     arr_start = []
#     arr_end = []
#     arr_payload_data  = []
#     arr_sum_payload = []
#     arr_cal_check = []
#     arr_payload_checksum = []
    
#     frame_num = 1
#     for _ in range(total_frames):
#         start_index = (frame_num - 1) * 8
#         # print(start_index)
#         # arr_start.append(start_index)
#         end_index = min(frame_num * 8, len(file_data))
#         # print(end_index)
#         # arr_end.append(end_index)
#         payload = file_data[start_index:end_index]
#         # arr_payload_data.append(payload)
#         # arr_cal_check.append(checksum)
#         payload = bytes(payload)
#         print(payload)
#         # arr_payload_data.append(payload)

#         try:
#             send_payload(ser, 68, 3, frame_num, *payload)
            
#             # Increment frame_num and handle rollback
#             frame_num += 1
#             if frame_num >= 255:
#                 frame_num = 1

#             # Calculate percentage based on total_frames and current frame_num
#             percentage = ((frame_num - 1) / total_frames) * 100
#             progress_label.config(text=f"Progress: {percentage:.2f}%")
#             # print(arr_start[:11])
#             # print("---------------------------------------------------------------------")
            
#             # print(arr_end[total_frames-start_index:total_frames])
#             # print("---------------------------------------------------------------------")
            
#             # print(payload[:7])
#             # print("---------------------------------------------------------------------")
            
#             # print(arr_payload_data)
#             # print("---------------------------------------------------------------------")
            
#             # print(arr_sum_payload)
#             # print("---------------------------------------------------------------------")
#             # print(arr_cal_check)
#             # print("---------------------------------------------------------------------")
#             # print(arr_payload_checksum)
#             # print("---------------------------------------------------------------------")
#         except serial.SerialException as e:
#             print(f"Error writing to serial port: {e}")
#             break

#     print("Firmware flashing completed.")
#     ser.close()


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




# def erase_memory_payload(ser, main_id, sequence_id, *payload_bytes):
#     payload = bytearray([main_id, sequence_id]) + bytearray(payload_bytes)
#     checksum = bytearray([main_id, sequence_id]) + bytearray(payload_bytes)
#     print(checksum)
#     payload += bytes([checksum])
#     ser.write(payload)
#     print(f"Checksum Payload: {payload}")
#     print(ser, main_id, sequence_id, *payload_bytes)
#     print(f"Erase Memory Payload: {payload}")
    
    
    
    
    
    
# def send_program_size_payload(ser,main_id,sequence_id,*payload_bytes):
#     payload = bytearray([main_id, sequence_id]) + bytearray(payload_bytes)
#     checksum = cal_checksum(bytearray([main_id, sequence_id]) + bytearray(payload_bytes))
#     payload += bytes([checksum])
#     ser.write(payload)
#     print(f"Program Size Payload: {payload}")





def process_feedback(data):
    if len(data) != 8:
        print("Invalid feedback payload length")
        return

    feedback_id = data[1]
    d1 = data[2]
    d2 = data[3]
    d3 = data[4]
    d4 = data[5]
    checksum = data[6]

    calculated_checksum = sum(data[1:6]) & 0xFF  # Calculate checksum using XOR
    if calculated_checksum != checksum:
        print("Checksum mismatch")
        return

    feedback_messages = {
        1: "Erased Successful",
        2: "Erase Failure",
        3: f"Frame Received (Requested Frame Number: {d1})",
        4: "Frame Receive Failure",
        5: f"Checksum Data (Checksum Value: {d1}{d2}{d3}{d4})",
        6: f"Program Size Received ({d1} bytes)",
        7: "Flashed Status Received",
        8: "App Sign failure"
    }

    if feedback_id in feedback_messages:
        feedback_message = feedback_messages[feedback_id]
        print(f"Feedback ID: {feedback_id} - {feedback_message}")
        # Here, you can add code to display the feedback message to the user or perform other actions based on the feedback received.
    else:
        print(f"Unknown Feedback ID: {feedback_id}")

def listen_feedback():
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return

    try:
        while True:
            if ser.in_waiting >= 8:
                incoming_data = ser.read(8)
                process_feedback(incoming_data)
    finally:
        ser.close()  # Close the serial port when done

def erase_memory():
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    try:
        send_payload(ser, 68, 1, 90, 90, 90, 90, 90, 90, 90, 90, 90)
        listen_feedback()  # Start listening for feedback after sending erase payload
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    finally:
        ser.close()

# Modify other functions (like flash_firmware_thread, program_size, etc.) similarly to listen for feedback after sending the respective payload.







import tkinter as tk
from tkinter import filedialog
import serial.tools.list_ports
import serial
import math
import threading
import time

# Global variables
baudrate = 9600

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

def listen_inputs(callback):
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    
    try:
        while True:
            if ser.in_waiting > 0:
                incoming_data = ser.read(ser.in_waiting)
                callback(incoming_data)
            time.sleep(0.1)  # Add a small delay to avoid high CPU usage in the loop
    finally:
        ser.close()  # Close the serial port when done

def process_feedback(data):
    if len(data) != 8:
        print("Invalid feedback payload length")
        return

    feedback_id = data[1]
    d1 = data[2]
    d2 = data[3]
    d3 = data[4]
    d4 = data[5]
    checksum = data[6]

    calculated_checksum = sum(data[1:6]) & 0xFF  # Calculate checksum using XOR
    if calculated_checksum != checksum:
        print("Checksum mismatch")
        return

    feedback_messages = {
        1: "Erased Successful",
        2: "Erase Failure",
        3: f"Frame Received (Requested Frame Number: {d1})",
        4: "Frame Receive Failure",
        5: f"Checksum Data (Checksum Value: {d1}{d2}{d3}{d4})",
        6: f"Program Size Received ({d1} bytes)",
        7: "Flashed Status Received",
        8: "App Sign failure"
    }

    if feedback_id in feedback_messages:
        feedback_message = feedback_messages[feedback_id]
        print(f"Feedback ID: {feedback_id} - {feedback_message}")
    else:
        print(f"Unknown Feedback ID: {feedback_id}")

def listenUltraProxMax():
    listen_inputs(process_feedback)

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
    
    feedback_button = tk.Button(window, text="feedback lelo", command=listenUltraProxMax)
    feedback_button.pack()
    
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




















import tkinter as tk
from tkinter import filedialog
import serial.tools.list_ports
import serial
import math
import threading
import time

# Global variables
baudrate = 9600

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

def listen_inputs(callback):
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    
    try:
        while True:
            if ser.in_waiting > 0:
                incoming_data = ser.read(ser.in_waiting)
                callback(incoming_data)
            time.sleep(0.1)  # Add a small delay to avoid high CPU usage in the loop
    finally:
        ser.close()  # Close the serial port when done

def process_feedback(data):
    if len(data) != 8:
        print("Invalid feedback payload length")
        return

    feedback_id = data[1]
    d1 = data[2]
    d2 = data[3]
    d3 = data[4]
    d4 = data[5]
    checksum = data[6]

    calculated_checksum = sum(data[1:6]) & 0xFF  # Calculate checksum using XOR
    if calculated_checksum != checksum:
        print("Checksum mismatch")
        return

    feedback_messages = {
        1: "Erased Successful",
        2: "Erase Failure",
        3: f"Frame Received (Requested Frame Number: {d1})",
        4: "Frame Receive Failure",
        5: f"Checksum Data (Checksum Value: {d1}{d2}{d3}{d4})",
        6: f"Program Size Received ({d1} bytes)",
        7: "Flashed Status Received",
        8: "App Sign failure"
    }

    if feedback_id in feedback_messages:
        feedback_message = feedback_messages[feedback_id]
        print(f"Feedback ID: {feedback_id} - {feedback_message}")
    else:
        print(f"Unknown Feedback ID: {feedback_id}")

def listenUltraProxMax():
    threading.Thread(target=listen_inputs, args=(process_feedback,)).start()

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
    
    # Call listenUltraProxMax function to start listening for feedback automatically
    listenUltraProxMax()
    
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













import tkinter as tk
from tkinter import filedialog
import serial.tools.list_ports
import serial
import math
import threading
import time

# Global variables
baudrate = 9600

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

def listen_inputs(callback):
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    
    try:
        while True:
            if ser.in_waiting > 0:
                incoming_data = ser.read(ser.in_waiting)
                callback(incoming_data)
            time.sleep(0.1)  # Add a small delay to avoid high CPU usage in the loop
    finally:
        ser.close()  # Close the serial port when done

def process_feedback(data):
    if len(data) != 8:
        print("Invalid feedback payload length")
        return

    feedback_id = data[1]
    d1 = data[2]
    d2 = data[3]
    d3 = data[4]
    d4 = data[5]
    checksum = data[6]

    calculated_checksum = sum(data[1:6]) & 0xFF  # Calculate checksum using XOR
    if calculated_checksum != checksum:
        print("Checksum mismatch")
        return

    feedback_messages = {
        1: "Erased Successful",
        2: "Erase Failure",
        3: f"Frame Received (Requested Frame Number: {d1})",
        4: "Frame Receive Failure",
        5: f"Checksum Data (Checksum Value: {d1}{d2}{d3}{d4})",
        6: f"Program Size Received ({d1} bytes)",
        7: "Flashed Status Received",
        8: "App Sign failure"
    }

    if feedback_id in feedback_messages:
        feedback_message = feedback_messages[feedback_id]
        feedback_label.config(text=feedback_message)  # Update label with feedback message
        print(f"Feedback ID: {feedback_id} - {feedback_message}")
    else:
        print(f"Unknown Feedback ID: {feedback_id}")

def listenUltraProxMax():
    threading.Thread(target=listen_inputs, args=(process_feedback,)).start()

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
    
    # Create a label to display feedback messages
    global feedback_label
    feedback_label = tk.Label(window, text="", wraplength=300)
    feedback_label.pack()
    
    # Call listenUltraProxMax function to start listening for feedback automatically
    listenUltraProxMax()
    
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
