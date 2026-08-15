import sys
import json
from services.database import (DB_Get_Connection, DB_Save_All_VIP_Variable, DB_Create_Table_VIP_Variable, DB_Drop_Table_VIP_Variable, DB_Create_Table_Variable, DB_Save_All_Variable, DB_Get_All_Variable, DB_Get_All_VIP_Variable, DB_Drop_Table_Variable)
from services.logic import (set_Variable_Logic, set_VIP_Variable_Logic)

task = sys.argv[1] if len(sys.argv) > 1 else None
key = sys.argv[2] if len(sys.argv) > 2 else None

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
            data = DB_Get_All_Variable()
            response(
                "success",
                "berhasil mengambil variables",
                data
            )
        elif key == "vip_variables":
            data = DB_Get_All_VIP_Variable()
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
        conn = DB_Get_Connection()

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
                DB_Drop_Table_Variable(conn)
                DB_Create_Table_Variable(conn)
                DB_Save_All_Variable(data, conn)
            elif key == "vip_variables":
                DB_Drop_Table_VIP_Variable(conn)
                DB_Create_Table_VIP_Variable(conn)
                DB_Save_All_VIP_Variable(data, conn)
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
        
        conn = DB_Get_Connection()
        
        try:
            data = json.loads(sys.stdin.read())
        
            if key == "variables":
                result = set_Variable_Logic(data["content"], "AgACAgUAAxkBAAIJy2mAQ6YD5c-ROy_-XEc2x_08trF8AAIoDmsbc3UBVP_H7wRWov5EAQADAgADeQADOAQ")
            elif key == "vip_variables":
                result = set_VIP_Variable_Logic(data["content"], None)
                
            conn.commit()
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