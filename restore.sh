echo "====== STARTING RESTORE PROGRAM ======"

nano restore.json

python services/manual_restore.py

rm restore.json

echo "====== COMPLETE RESTORE PROGRAM ======"