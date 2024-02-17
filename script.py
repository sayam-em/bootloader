import tkinter as tk
from tkinter import filedialog
import serial.tools.list_ports
import serial
import math

# def open_serial_port():
#     try:
#         for port in serial.tools.list_ports.comports():
#             try:
#                 print(f"Serial port {port.device} successfully opened")
#             except serial.SerialException as e:
#                 print(f"Error opening serial port {port.device}: {e}")
#         print("Failed to open any serial port")
#         return None
#     except Exception as e:
#         print(f"Error opening the serial port : {e}")
#         return None



# open_serial_port()

# def list_usb_devices():
#     for port in serial.tools.list_ports.comports():
#         if "COM3" in port.description:
#             usb = port.device
#             return usb
#     return usb

# usb_devices = list_usb_devices()

# print(usb_devices)


# def get_ports():
#     return [port.device for port in serial.tools.list_ports.comports()]



def get_usb_ports():
    for port in serial.tools.list_ports.comports():
        if 'COM4' in port.description:
            print(port.device)
            return port.device
    return port.device



def import_file(file_label):
    file_path = filedialog.askopenfilename()
    if file_path:
        file_label.config(text="Selected File: " + file_path)
        return file_path
    return None


def open_serial_port(baudrate):
    try:
        ser = serial.Serial(get_usb_ports(),baudrate )
        return ser
    except Exception as e:
        print(f"Error opening the serial port : {e}")
        return None
    
# def close_serial_port(ser):
#     if ser:
#         ser.close()
        
        
# def flash_firmware(ser, file_path):
#     if not file_path:
#         print(f"Please select a file")
#         return
#     flash_firmware(ser, file_path)


def flash_firmware(file_path, baudrate,percentage_label):
    if not file_path:
        print("Please select a file")
        return

    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
    except FileNotFoundError:
        print(f"File {file_path} not found")
        return

    ser_port = get_usb_ports()
    if not ser_port:
        print("COM3 port not found")
        return
    
    
    # ser = serial.Serial()
    # ser.baudrate = 9600
    # ser.port = "COM4"
    # ser.open()
    
    
    
    # ser = serial.Serial(ser_port, baudrate)
  
    # print(ser)
    
    
    try:
        ser = serial.Serial(ser_port, baudrate)
        ser.open()
        print(ser)
    except Exception as e:
        print(f"Error opening the serial port: {e}")
        return

    frame_num = 1
    # print(frame_num)
    
    total_frames = math.ceil(len(file_data) / 7)
    # print(total_frames)
    # print(file_data)
    arr_start = []
    arr_end = []
    arr_payload_data  = []
    arr_sum_payload = []
    arr_cal_check = []
    arr_payload_checksum = []

    for frame_num in range(1, total_frames + 1):
        
        start_index = (frame_num - 1) * 7
        # print(start_index)
        # arr_start.append(start_index)
        
        end_index = min(frame_num * 7, len(file_data))
        # print(end_index)
        # arr_end.append(end_index)
        
        payload = file_data[start_index:end_index]
        
        # arr_payload_data.append(payload)
        
        
        
        
        
        checksum = sum(payload) & 0xFF  # Calculate checksum
        # print(checksum)
        
        # arr_sum_payload.append(sum(payload))
        
        # arr_cal_check.append(checksum)
        
        
        
        payload += bytes([checksum])  # Add checksum to payload
        
        # arr_payload_checksum.append(payload)

        # Send payload over UART with frame number
        transfer_data_payload(ser, 68, 3, frame_num, *payload)
        frame_num = (frame_num % 255) + 1
        
        percentage = (frame_num / total_frames) * 100

        # Update tkinter GUI with percentage
        show_percentage(percentage, percentage_label)
        # print(frame_num)
        # print(payload)
        # print(sum(payload))
    # print(arr_start[:10])
    # print(arr_end[total_frames-start_index:total_frames])
    # print(payload[:7])
    # print(arr_payload_data)
    # print(arr_sum_payload)
    # print("---------------------------------------------------------------------")
    # print(arr_cal_check)
    # print("---------------------------------------------------------------------")
    # print(arr_payload_checksum)
    # print("---------------------------------------------------------------------")
    print("Firmware flashing completed")
    ser.close()




def transfer_data_payload(ser, main_id, sequence_id, frame_num, *payload_bytes):
    payload = bytearray([main_id, sequence_id, frame_num]) + bytearray(payload_bytes)
    ser.write(payload)
    print(f"Transferred Data: {payload}")
    
def show_percentage(percentage, label):
    label.config(text=f"Progress: {percentage:.2f}%")

# def read_file(file_path):
#     try:
#         with open(file_path, "r") as file:
#             file_contents = file.read()
#         return file_contents
#     except FileNotFoundError:
#         print('File not Found')
#         return None
#     except Exception as e:
#         print('An exception occurred:', e)
#         return None

def flash_file(file_label):
 f = open(import_file(file_label), mode="rb")
 f.close()

def bootloader_payload_format(main_id, sequence_id, d1, d2, d3, d4, d5, d6, d7, d8, checksum):
    print("Bootloader Payload Format:")
    print(f"Main ID: {main_id}")
    print(f"Sequence ID: {sequence_id}")
    print(f"D1: {d1}")
    print(f"D2: {d2}")
    print(f"D3: {d3}")
    print(f"D4: {d4}")
    print(f"D5: {d5}")
    print(f"D6: {d6}")
    print(f"D7: {d7}")
    print(f"D8: {d8}")
    print(f"Checksum: {checksum}")

def main_id_transmission(server_transmit_id, server_receive_id):
    print("Main ID:")
    print(f"Server transmits data with Main ID: {server_transmit_id}")
    print(f"Server receives data with Main ID: {server_receive_id}")





def feedback(feedback_id):
    feedback_messages = {
        1: "Erased Successful",
        2: "Erase Failure",
        3: "Frame Received",
        4: "Frame Receive Failure",
        5: "Checksum Data",
        6: "Program Size Received"
    }

    if feedback_id in feedback_messages:
        feedback_message = feedback_messages[feedback_id]
        print(f"Feedback ID: {feedback_id} - {feedback_message}")
    else:
        print(f"Invalid Feedback ID: {feedback_id}")

def bootloader_flow_control(sequence_number):
    flow_control_messages = {
        0: {"Info": "SNA", "Client": "-", "Server": "-"},
        1: {"Info": "Erase Memory", "Client": "Tx", "Server": "Rx"},
        2: {"Info": "Program Size", "Client": "Tx", "Server": "Rx"},
        3: {"Info": "Transfer Data", "Client": "Tx", "Server": "Rx"},
        4: {"Info": "Checksum", "Client": "Tx", "Server": "Rx"},
        5: {"Info": "Reset", "Client": "Tx", "Server": "Rx"},
        6: {"Info": "Feedback", "Client": "Rx", "Server": "Tx"}
    }
    if sequence_number in flow_control_messages:
        message = flow_control_messages[sequence_number]
        print(f"Sequence Number (ID): {sequence_number}")
        print(f"Info: {message['Info']}")
        print(f"Client: {message['Client']}")
        print(f"Server: {message['Server']}")
    else:
        print(f"Invalid Sequence Number (ID): {sequence_number}")

def erase_memory_payload(main_id, sequence_id, *payload_bytes, checksum):
    print("Erase Memory Payload(10 bytes):")
    print(f"Main ID: {main_id}")
    print(f"Sequence ID: {sequence_id}")
    print("Payload Bytes:")
    for i, byte in enumerate(payload_bytes):
        print(f"D{i+1}: {hex(byte)}")
    print(f"Checksum: {checksum}")

def program_size_payload(main_id, sequence_id, *args, checksum):
    print("Program Size Payload (10 bytes):")
    print(f"Main ID: {main_id}")
    print(f"Sequence ID: {sequence_id}")
    print("Program Size:")
    program_sizes = args[:5]
    for i, size in enumerate(program_sizes):
        print(f"Program Size {i}: {size}")
    print("Payload Bytes:")
    payload_bytes = args[5:-1]
    for byte in payload_bytes:
        print(f"Payload Byte: {hex(byte)}")
    print(f"Checksum: {checksum}")


# def transfer_data_payload(main_id, sequence_id, frame_num, *payload_bytes, checksum):
#     print("Transfer Data Payload(10 bytes):")
#     print(f"Main ID: {main_id}")
#     print(f"Sequence ID: {sequence_id}")
#     print(f"Frame Num: {frame_num}")
#     print("Payload Bytes:")
#     for i, byte in enumerate(payload_bytes):
#         print(f"D{i+1}: {byte}")
#     print(f"Checksum: {checksum}")


def checksum_payload(main_id, sequence_id, *payload_bytes, checksum):
    print("Checksum Payload(10 bytes):")
    print(f"Main ID: {main_id}")
    print(f"Sequence ID: {sequence_id}")
    print("Payload Bytes:")
    for i, byte in enumerate(payload_bytes):
        print(f"D{i+1}: {hex(byte)}")
    print(f"Checksum: {checksum}")


def ecu_reset_payload(main_id, sequence_id, *payload_bytes, checksum):
    print("ECU Reset Payload(10 bytes):")
    print(f"Main ID: {main_id}")
    print(f"Sequence ID: {sequence_id}")
    print("Payload Bytes:")
    for i, byte in enumerate(payload_bytes):
        print(f"D{i+1}: {hex(byte)}")
    print(f"Checksum: {checksum}")


def feedback_payload(main_id, feedback_id, *payload_bytes, checksum):
    print("Feedback Payload(7 bytes):")
    print(f"Main ID: {main_id}")
    print(f"Feedback ID: {feedback_id}")
    print("Payload Bytes:")
    for i, byte in enumerate(payload_bytes):
        print(f"D{i+1}: {byte}")
    print(f"Checksum: {checksum}")


def main():
    
     
    window = tk.Tk()
    window.title("Bootloader")
    window.geometry("400x400")
    
    
    serial_port = open_serial_port(9600)
    
    

    main_container = tk.Frame(window)

    nav_frame = tk.Frame(main_container)
    nav_label = tk.Label(nav_frame, text="BootLoader Flashing", foreground="white", background="black", width=100)
    nav_label.pack(fill=tk.BOTH, expand=True)
    

    

    container_frame = tk.Frame(main_container)
    
    button_connected = tk.Button(container_frame, text=f"Connected device: {get_usb_ports()}", width=25, height=5, bg="blue", fg="yellow", command=get_usb_ports())
    button_connected.pack(pady=10)

    file_label = tk.Label(container_frame, text="", foreground="black", background="white")
    file_label.pack()

    button_import = tk.Button(container_frame, text="Import File", width=25, height=5, bg="blue", fg="yellow", command=lambda: import_file(file_label))
    button_import.pack(pady=10)
    
    
    percentage_label = tk.Label(container_frame, text="Progress: 0.00%", foreground="black", background="white")
    percentage_label.pack()

    flash_button = tk.Button(window, text="Flash Firmware", command=lambda: flash_firmware(file_label.cget("text")[15:], 9600, percentage_label))
    flash_button.pack()
    
    
    # flash_button = tk.Button(window, text="Flash Firmware", command=lambda: flash_firmware(file_label.cget("text")[15:], 9600))

    # # flash_button = tk.Button(window, text="Flash Firmware", command=lambda: flash_firmware(file_label.cget("text")[14:], 9600))
    # flash_button.pack()

    # flash_button = tk.Button(window, text="Flash Firmware", command=lambda: flash_firmware(serial_port, file_label))
    # button_read = tk.Button(container_frame, text="Read File", width=25, height=5, bg="blue", fg="yellow", command=read_file())
    # button_read.pack(pady=10)

    # button_flash = tk.Button(container_frame, text="Flash File", width=25, height=5, bg="blue", fg="yellow", command=lambda: flash_file(file_label))
    # button_flash.pack(pady=10)

    footer_frame = tk.Frame(main_container)
    footer_label = tk.Label(footer_frame, text="EMotorad", foreground="white", background="green", width=100)
    footer_label.pack(fill=tk.BOTH, expand=True)

    nav_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    container_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    footer_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    main_container.pack(fill=tk.BOTH, expand=True)
    

    # window.after(5000, update_connection_status)

    window.mainloop()
    # close_serial_port(serial_port)

if __name__ == "__main__":
    main()




