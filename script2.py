async def earse_payload():
\
    
    if not ser:
        print("Serial port not available.")
        return
    
    for _ in range(8):
        print(_)
        start_index = (frame_num - 1) * 8
        # print(start_index)
        # arr_start.append(start_index)
        end_index = min(frame_num * 8, len(file_data))
        # print(end_index)
        # arr_end.append(end_index)
        payload = file_data[start_index:end_index]
        # arr_payload_data.append(payload)
        checksum = sum(payload) & 0xFF
        # arr_cal_check.append(checksum)
        payload += bytes([checksum])
        # arr_payload_data.append(payload)

        try:
            transfer_data_payload(ser, 68, 3, frame_num, *payload)
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




def send_program_size_payload(ser,main_id,sequence_id,*payload_bytes):
    payload = bytearray([main_id, sequence_id]) + bytearray(payload_bytes)
    checksum = cal_checksum(*payload)
    payload += bytes([checksum])
    ser.write(payload)
    print(f"Program Size Payload: {payload}")
    
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
                send_program_size_payload(ser, 68, 2, size_byte_1, size_byte_2, size_byte_3, size_byte_4, 0x5A, 0x5A, 0x5A, 0x5A)
            except serial.SerialException as e:
                print(f"Error writing to serial port: {e}")
            finally:
                ser.close()
    print("Program Size command sent.")