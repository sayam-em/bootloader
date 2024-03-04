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

def file():
    upload_file()


def import_file(file_label):
    return lambda: upload_file(file_label)



def cal_checksum(*payload_bytes):
    print(*payload_bytes)
    checksum = payload_bytes[0]
    for byte in payload_bytes[1:]:  
        checksum ^= byte
    print(checksum)
    return checksum


def send_checksum_payload(ser, main_id, sequence_id, *payload_bytes):
    before_check_sum = [main_id, sequence_id, *payload_bytes]
    print(before_check_sum)
    
    checksum = cal_checksum(*before_check_sum)
    print(checksum)
    payload = before_check_sum + [checksum] 
    print(payload)
    ser.write(payload)
    print(ser, main_id, sequence_id, *payload_bytes)
    print(f"Checksum Payload: {payload}")
    
    
def checksum_payload():
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    try:
        send_checksum_payload(ser, 68, 4,90,90,90,90,90,90,90,90,90)
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    print("Checksum payload sent.")
    ser.close()



def send_payload(ser, main_id, sequence_id, *payload_bytes):
    print(f"vanilla payload {payload_bytes}")

    before_check_sum = [main_id, sequence_id, *payload_bytes]
    
    checksum = cal_checksum(*before_check_sum)
    print(f"checksum {checksum}")

    payload = before_check_sum + [checksum] 
    print(f"after adding checksum {payload}")

    ser.write(payload)
    print(ser, main_id, sequence_id, *payload_bytes)
    print(f"Payload sent: {payload}")


async def flash_firmware(file_label_text, baudrate, progress_label):
    # Check file label format
    file_prefix = "Selected File: "
    if not file_label_text.startswith(file_prefix):
        print("Invalid file label format.")
        return

    # Extract file path
    file_path = file_label_text[len(file_prefix):]
    if not file_path:
        print("Please select a file.")
        return

    print(f"File path: {file_path}")  # Debugging print statement

    try:
        # Read file data
        with open(file_path, "rb") as f:
            file_data = f.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return
    except Exception as e:
        print(f"Error opening file: {e}")
        return

    # Open serial port
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return

    print(f"vanilla length of file: {len(file_data)}")
    total_frames = math.ceil(len(file_data) / 8)
    print(f"After ceiling to the next number {total_frames}")

    # Loop through frames and send data
    progress = 0
    frame_num = 1
    payload_size = 7  # Adjust payload size according to your protocol
    while frame_num <= total_frames:
        start_index = (frame_num - 1) * payload_size
        end_index = min(start_index + payload_size, len(file_data))
        payload = file_data[start_index:end_index]

        try:
            send_payload(ser, 68, 3, frame_num, *payload)
            await asyncio.sleep(0.25)  # Delay for stability
            
            # Wait for feedback
            while True:
                if ser.in_waiting > 0:
                    incoming_data = ser.read(ser.in_waiting)
                    print(f"incoming data: {incoming_data}")
                    await process_feedback(incoming_data)
                    break
                await asyncio.sleep(0.05)  # Wait for feedback
        except serial.SerialException as e:
            print(f"Error writing to serial port: {e}")
            break
        
        frame_num += 1
        progress = (frame_num / total_frames) * 100
        progress_label.config(text=f"Progress: {progress:.2f}%")

    print("Firmware flashing completed.")
    ser.close()

def transfer_data_payload(ser, main_id, sequence_id, frame_num, *payload_bytes):
    start_time = time.time()
    before_check_sum = [main_id, sequence_id, *payload_bytes]
    
    checksum = cal_checksum(*before_check_sum)
    print(checksum)
    payload = before_check_sum + [checksum] 
    print(payload)
    ser.write(payload)
    print(ser, main_id, sequence_id, *payload_bytes)
    print(f"Transfer Data payload Payload: {payload}")
    end_time = time.time()  
    elapsed_time = end_time - start_time
    print(f"Time taken: {elapsed_time} seconds")


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
                send_payload(ser, 68, 2, size_byte_1, size_byte_2, size_byte_3, size_byte_4,90,90,90,90)
            except serial.SerialException as e:
                print(f"Error writing to serial port: {e}")
            finally:
                ser.close()
    print("Program Size command sent.")
        
    
def erase_memory():
    ser = open_serial_port(baudrate)
    print(ser)
    if not ser:
        print("Serial port not available.")
        return
    try:
        send_payload(ser, 68, 1, 90, 90, 90, 90, 90, 90, 90, 90, 90)
        while True:
            if ser.in_waiting > 0:
                incoming_data = ser.read(ser.in_waiting)
                print(f"incoming data: {incoming_data}")
                process_feedback(incoming_data)
                break
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    print("Memory erase command sent.")
    ser.close()


    
    
def application_flashed_properly_payload():
    ser = open_serial_port(baudrate)
    
    if not ser:
        print("Serial port not available.")
        return
    
    try:
        send_payload(ser, 68, 7,90,90,90,90,90,90,90,90,90)
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
        send_payload(ser, 1, 20, 154, 154, 154, 154, 154, 154, 154, 154,  154, 154, 154, 154, 154, 154, 154, 154, 154)
    except serial.SerialException as e:
        print(f"Error writing to serial port: {e}")
    print("Display  payload command sent.")
    ser.close()
   





def listen_inputs(callback, feedback_label):
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    
    try:
        while True:
            if ser.in_waiting > 0:
                incoming_data = ser.read(ser.in_waiting)
                print(incoming_data + " incoming data")
                callback(incoming_data, feedback_label)
            t = time.localtime()
            current_time = time.strftime("%H:%M:%S", t)
            # print(current_time)
            time.sleep(0.05)
            t = time.localtime()
            current_time = time.strftime("%H:%M:%S", t)
            # print(current_time)
            print("after")
    finally:
        ser.close() 


# def listenUltraProxMax():
#     threading.Thread(target=listen_inputs, args=(process_feedback, feedback_label)).start()

async def listen(serial_port, callback, feedback_label):
    try:
        while True:
            if serial_port.in_waiting > 0:
                incoming_data = serial_port.read(serial_port.in_waiting)
                callback(incoming_data, feedback_label)
            await asyncio.sleep(0.05)
    except asyncio.CancelledError:
        print("Listening cancelled.")

def start_listening(serial_port, callback, feedback_label):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.create_task(listen(serial_port, callback, feedback_label))
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

def listenUltraProxMax():
    ser = open_serial_port(baudrate)
    if not ser:
        print("Serial port not available.")
        return
    try:
        start_listening(ser, process_feedback, feedback_label)
    except Exception as e:
        print(f"Error listening: {e}")

    
    


def send_next_frame(ser, frame_num, file_data):
    # Adjust the payload size according to your protocol
    payload_size = 7
    start_index = (frame_num - 1) * payload_size
    end_index = min(start_index + payload_size, len(file_data))
    payload = file_data[start_index:end_index]

    try:
        send_payload(ser, 68, 3, frame_num, *payload)
    except Exception as e:
        print(f"Error sending frame {frame_num}: {e}")





async def process_feedback(data):
    # Process feedback data
    if len(data) != 8:
        print("Invalid feedback payload length")
        return
    
    main_id = data[0]
    sub_id = data[1]
    feedback_id = data[2]
    d1 = data[3]
    d2 = data[4]
    d3 = data[5]
    d4 = data[6]
    checksum = data[7]

    feedback_messages = {
        1: "Erased Successful",
        2: "Erase Failure",
        3: f"Frame Received (Requested Frame Number: {d1})",
        4: "Frame Receive Failure",
        5: f"Checksum Data (Checksum Value: {d1},{d2},{d3},{d4})",
        6: f"Program Size Received ({d1} bytes)",
        7: "Flashed Status Received",
        8: "App Sign Failure"
    }

    if feedback_id in feedback_messages:
        feedback_message = feedback_messages[feedback_id]
        if feedback_id == 2:
            print("Repeating erase operation")
            await erase_memory()
        elif feedback_id == 3:
            print(f"Sending next requested frame: {d1}")
            threading.Thread(target=send_next_frame, args=(get_usb_port(), d1, file_data)).start()  # Automatically send the next frame
        elif feedback_id == 4:
            print("Resending the failed frame")
            # Resend the failed frame
            threading.Thread(target=send_failed_frame, args=(get_usb_port(), d1, file_data)).start()
        elif feedback_id == 5:
            checksum_feedback = cal_checksum(d1, d2, d3, d4)
            print(f"Received checksum: {checksum}, Calculated checksum: {checksum_feedback}")
            if checksum == checksum_feedback:
                print("Checksum verification successful. Proceed with data processing.")
            else:
                print("Checksum verification failed. Resend the frame or take appropriate action.")
        feedback_label.config(text=feedback_message) 
        print(f"Feedback ID: {feedback_id} - {feedback_message}")
    else:
        print(f"Unknown Feedback ID: {feedback_id}")
    
    print(f"Main ID: {main_id}, Sub ID: {sub_id}")
def send_failed_frame(ser, failed_frame_num, file_data):
    # Resend the failed frame
    payload_size = 7  # Adjust payload size according to your protocol
    start_index = (failed_frame_num - 1) * payload_size
    end_index = min(start_index + payload_size, len(file_data))
    payload = file_data[start_index:end_index]

    try:
        send_payload(ser, 68, 3, failed_frame_num, *payload)
    except Exception as e:
        print(f"Error resending frame {failed_frame_num}: {e}")

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
    
    # feedback_button = tk.Button(window, text="feedback lelo", command=listenUltraProxMax)
    # feedback_button.pack()
    
    
    
    global feedback_label
    feedback_label = tk.Label(window, text="", wraplength=300)
    feedback_label.pack()
    
    footer_frame = tk.Frame(main_container)
    footer_label = tk.Label(footer_frame, text="EMotorad", foreground="white", background="green", width=100)
    footer_label.pack(fill=tk.BOTH, expand=True)

    nav_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    container_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    footer_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    main_container.pack(fill=tk.BOTH, expand=True)

    # listenUltraProxMax()
    window.mainloop()

if __name__ == "__main__":
    main()
    
    
    
    
    
    
    
    