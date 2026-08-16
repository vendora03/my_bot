import sys, asyncio, time, json, socket
from services import database
from services import logic
from config import ADMIN_IDS

task = sys.argv[1] if len(sys.argv) > 1 else None
key = sys.argv[2] if len(sys.argv) > 2 else None

def Send_Message_Admin(message, file_id):
    data = json.dumps({
        "action": "send_message",
        "message": message,
        "file_id": file_id
    }).encode("utf-8")

    with socket.create_connection(("127.0.0.1", 8765)) as sock:
        sock.sendall(data)
        response = sock.recv(1024)

    return response.decode("utf-8")
    
def response(status, message, data=None):
    result = {
        "status": status,
        "message": message
    }

    if data is not None:
        result["data"] = data

    print(json.dumps(result))

match task:
    case "get_data":
        if key == "variables":
            data = database.DB_Get_All_Variable()
            response(
                "success",
                "berhasil mengambil variables",
                data
            )
        elif key == "vip_variables":
            data = database.DB_Get_All_VIP_Variable()
            response(
                "success",
                "berhasil mengambil vip_variables",
                data
            )
        else:
            response(
                "error",
                "key tidak dikenal"
            )
    case "post_data":
        if key not in ["variables", "vip_variables"]:
            response(
                "error",
                "key tidak dikenal"
            )
            sys.exit()
        conn = database.DB_Get_Connection()

        try:
            raw_data = json.loads(sys.stdin.read())
            data = [
                (
                    item["access_code"],
                    item["content"],
                    item["file_id"],
                    item["created_at"]
                )
                for item in raw_data
            ]
       
            if key == "variables":
                database.DB_Drop_Table_Variable(conn)
                database.DB_Create_Table_Variable(conn)
                database.DB_Save_All_Variable(data, conn)
            elif key == "vip_variables":
                database.DB_Drop_Table_VIP_Variable(conn)
                database.DB_Create_Table_VIP_Variable(conn)
                database.DB_Save_All_VIP_Variable(data, conn)
            conn.commit()
            response(
                "success",
                "data berhasil disimpan"
            )
        except Exception as e:
            conn.rollback()
            response(
                "error",
                str(e)
            )
        finally:
            conn.close()
    case "add_data":
        if key not in ["variables", "vip_variables"]:
            response(
                "error",
                "key tidak dikenal"
            )
            sys.exit()
        
        conn = database.DB_Get_Connection()
        
        try:
            data = json.loads(sys.stdin.read())
        
            if key == "variables":
                result = logic.Logic_Set_Variable(data["content"], data["file_id"])
            elif key == "vip_variables":
                result = logic.Logic_Set_VIP_Variable(data["content"], data["file_id"])
            
            conn.commit()
            
            Send_Message_Admin(data["content"], data["file_id"])
            time.sleep(5)
            Send_Message_Admin(result, None)
            
            response(
                "success",
                result
            )
        except Exception as e:
            conn.rollback()
            response(
                "error",
                str(e)
            )
        finally:
            conn.close()
    case _:
        response(
            "error",
            "task tidak dikenal"
        )