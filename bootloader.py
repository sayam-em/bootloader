import tkinter as tk
from tkinter import filedialog
import serial.tools.list_ports
import serial
import math
import asyncio
import threading
import time

# Define global variables
baudrate = 9600
file_data = None
feedback_label = None
payload_size = 8

# Function to get the USB port
def get_usb_port():
    for port in serial.tools.list_ports.comports():
        if 'COM5' in port.description: 
            return port.device
    return None

# Function to open the serial port
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

# Function to upload file data
def upload_file(file_label_text, baudrate=9600):
    global file_data
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

# Function to handle errors
def handle_error(message):
    print("Error:", message)

# Function to calculate checksum
def cal_checksum(*payload_bytes):
    # print(*payload_bytes)
    checksum = payload_bytes[0]
    for byte in payload_bytes[1:]:  
        checksum ^= byte
    # print(checksum)
    return checksum

# Function to send checksum payload
def checksum(ser, main_id, sequence_id, *payload_bytes):
    before_check_sum = [main_id, sequence_id, *payload_bytes]
    checksum = cal_checksum(*before_check_sum)
    payload = before_check_sum + [checksum] 
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    try:
        send_payload(ser, 68, 4, *payload)
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    print("Checksum payload sent.")
    ser.close()

# Function to send payload
def send_payload(ser, main_id, sequence_id, *payload_bytes):
    before_check_sum = [main_id, sequence_id, *payload_bytes]
    checksum = cal_checksum(*before_check_sum)
    payload = before_check_sum + [checksum] 
    ser.write(payload)

# Function to update progress
def update_progress(progress_label, progress):
    progress_label.config(text=f"Progress: {progress:.2f}%")

# Function to update feedback
def update_feedback(feedback_label, message):
    feedback_label.config(text=message)

# Asynchronous function to flash firmware and listen for feedback
async def flash_firmware(file_label_text, baudrate, progress_label):
    file_prefix = "Selected File: "
    if not file_label_text.startswith(file_prefix):
        print("Invalid file label format.")
        return

    file_path = file_label_text[len(file_prefix):]
    if not file_path:
        print("Please select a file.")
        return

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

    total_frames = math.ceil(len(file_data) / payload_size)
    frame_num = 1
    try:
        while frame_num <= total_frames:
            print(f"before anything frame number initial one and icrementing {frame_num}")
            start_index = (frame_num - 1) * payload_size
            print(f"start index frame increase udring the normal flash {start_index}")
            
            end_index = min(start_index + payload_size, len(file_data))
            print(f"start end_index frame increase udring the normal flash {end_index}")
            
            before_payload = file_data[start_index:end_index]
            print(f"before checksum payload in normal operation {before_payload}")

            try:
                send_payload(ser, 68, 3, frame_num, *before_payload)
                await asyncio.sleep(0.5)
            except serial.SerialException as e:
                print(f"Error writing to serial port: {e}")
                break
            
            percentage = ((frame_num - 1) / total_frames) * 100
            progress_label.config(text=f"Progress: {percentage:.2f}%")

            # frame_num += 1
            await asyncio.sleep(0.5)
            if ser.in_waiting >= 8:
                print(f"kya sun rha h? {ser.in_waiting}")
                incoming_data = ser.read(8)
                print(f"Jo bhi data mil rha h {incoming_data}")
                main_id = incoming_data[0]
                sub_id = incoming_data[1]
                feedback_id = incoming_data[2]
                d1 = incoming_data[3]
                d2 = incoming_data[4]
                d3 = incoming_data[5]
                d4 = incoming_data[6]
                checksum = incoming_data[7]
                if main_id == 67:
                    if feedback_id == 2:
                        print("Repeating erase operation")
                        await erase_memory()
                    elif feedback_id == 3:
                        print(f"Sending next requested frame: {d1}")
                        send_next_frame(ser, d1, file_data)
                    elif feedback_id == 4:
                        print("Resending the failed frame")
                        send_failed_frame(ser, d1, file_data)
                    elif feedback_id == 5:
                        checksum_feedback = cal_checksum(d1, d2, d3, d4)
                        print(f"Received checksum: {checksum}, Calculated checksum: {checksum_feedback}")
                        if checksum == checksum_feedback:
                            print("Checksum verification successful. Proceed with data processing.")
                        else:
                            print("Checksum verification failed. Resend the frame or take appropriate action.")
                    feedback_label.config(text=f"Feedback ID: {feedback_id}")
            flash_firmware(file_label_text, baudrate, progress_label)

    finally:
        print("Firmware flashing completed.")
        ser.close()



# Function to start the flash firmware task in a separate thread
def flash_firmware_thread(file_label_text, baudrate, progress_label):
    threading.Thread(target=asyncio.run, args=(flash_firmware(file_label_text, baudrate, progress_label),)).start()

# Function to reset firmware
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

# Function to send ECU reset payload
def ecu_reset_payload(ser, main_id, sequence_id, *payload_bytes):
    before_check_sum = [main_id, sequence_id, *payload_bytes]
    checksum = cal_checksum(*before_check_sum)
    payload = before_check_sum + [checksum] 
    ser.write(payload)
    print(ser, main_id, sequence_id, *payload_bytes)

# Function to calculate program size
def calculate_program_size(file_label_text):
    file = upload_file(file_label_text)
    program_size = len(file)
    return program_size

# Function to calculate total frames
def total_frame(file_label_text):
    size = calculate_program_size(file_label_text)
    total_frames = math.ceil(size / 8)
    return total_frame

# Function to break down program size
def break_down_program_size(file_label_text):
    program_size = calculate_program_size(file_label_text)
    size_byte_1 = program_size & 0xFF
    size_byte_2 = (program_size >> 8) & 0xFF
    size_byte_3 = (program_size >> 16) & 0xFF
    size_byte_4 = (program_size >> 24) & 0xFF
    return size_byte_1, size_byte_2, size_byte_3, size_byte_4

# Function to send program size command
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
                send_payload(ser, 68, 2, size_byte_1, size_byte_2, size_byte_3, size_byte_4, 90, 90, 90, 90)
            except serial.SerialException as e:
                print(f"Error writing to serial port: {e}")
            finally:
                ser.close()
    print("Program Size command sent.")

# Function to erase memory
def erase_memory():
    ser = open_serial_port(baudrate)
    print(ser)
    if not ser:
        print("Serial port not available.")
        return
    try:
            send_payload(ser, 68, 1, 90, 90, 90, 90, 90, 90, 90, 90, 90)
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    print("Memory erase command sent.")
    ser.close()

# Function to send application flashed properly payload
def application_flashed_properly_payload():
    ser = open_serial_port(baudrate)
    
    if not ser:
        print("Serial port not available.")
        return
    
    try:
        send_payload(ser, 68, 7, 90, 90, 90, 90, 90, 90, 90, 90, 90)
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    finally:
        ser.close()

    print("Application Flashed Properly Payload sent.")

# Function to display
def display():
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    try:
        send_payload(ser, 1, 20, 154, 154, 154, 154, 154, 154, 154, 154,  154, 154, 154, 154, 154, 154, 154, 154, 154)
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    print("Display payload command sent.")
    ser.close()

# Function to send next frame
def send_next_frame(ser, frame_num, file_data):
    frame_num += 1
    print(f"after the next frame thing frame increase after send_next_frame{frame_num}")
    start_index = (frame_num - 1) * payload_size
    print(f"start index increase after send_next_frame {start_index}")
    
    end_index = min(start_index + payload_size, len(file_data))
    print(f"end index increase after send_next_frame  {end_index}")
    
    payload = file_data[start_index:end_index]
    print(f"after the whole fiasco paylaod before checksum in send_next_frame {payload}")

    try:
        send_payload(ser, 68, 3, frame_num, *payload)
        
    except Exception as e:
        print(f"Error sending frame {frame_num}: {e}")

# Function to send failed frame
def send_failed_frame(ser, failed_frame_num, file_data):
    start_index = (failed_frame_num - 1) * payload_size
    print(f"after the next frame thing frame increase after send_failed_frame{failed_frame_num}")
    
    end_index = min(start_index + payload_size, len(file_data))
    print(f"end index increase after send_failed_frame {end_index}")
    
    payload = file_data[start_index:end_index]
    print(f"after the whole fiasco paylaod before checksum send_failed_frame {payload}")

    try:
        send_payload(ser, 68, 3, failed_frame_num, *payload)
    except Exception as e:
        print(f"Error resending frame {failed_frame_num}: {e}")

# Function to import file
def import_file(file_label):
    file_path = filedialog.askopenfilename()
    if file_path:
        file_label.config(text="Selected File: " + file_path)
    else:
        print("No file selected.")
    return file_path

# Main function to create GUI and run event loop
async def main():
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
    flash_button = tk.Button(window, text="Flash Firmware", command=lambda: flash_firmware_thread(file_label.cget("text"), 9600, progress_label))
    flash_button.pack()
    
    reset_button = tk.Button(window, text="Reset Firmware", command=reset_firmware)
    reset_button.pack()
    
    erase_button = tk.Button(window, text="Erase Memory", command=erase_memory)
    erase_button.pack()
    
    program_size_button = tk.Button(window, text="Program Size", command=lambda: program_size(file_label.cget("text")))
    program_size_button.pack()
    
    checksum_button = tk.Button(window, text="Checksum Payload", command=checksum)
    checksum_button.pack()
    
    app_flashed_button = tk.Button(window, text="Application Flashed Properly", command=application_flashed_properly_payload)
    app_flashed_button.pack()
    
    display_button = tk.Button(window, text="Display Flashed Properly", command=display)
    display_button.pack()
    
    feedback_label = tk.Label(window, text="", wraplength=300)
    feedback_label.pack()
    
    footer_frame = tk.Frame(main_container)
    footer_label = tk.Label(footer_frame, text="EMotorad", foreground="white", background="green", width=100)
    footer_label.pack(fill=tk.BOTH, expand=True)

    nav_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    container_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    footer_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    main_container.pack(fill=tk.BOTH, expand=True)

    window.mainloop()

if __name__ == "__main__":
    asyncio.run(main())
