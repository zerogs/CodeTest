config = dict(
    DEBUG= True,
    SECRET_KEY='c6bbe7faa2b688f5481234958f836eb7',
    PONY={
        'provider': 'postgres',
        'user': 'postgres',
        'password': '534377a',
        'host': 'localhost',
        'database': 'dproject',
    },
    UPLOADS_DEFAULT_DEST='D://files/default/',
    UPLOADS_DEFAULT_URL ='http://localhost:5000/files/default/',

    UPLOADED_DATA_DEST='D://files/group_lists/',
    UPLOADED_DATA_URL='http://localhost:5000/files/group_lists/',

    UPLOADED_SCRIPTS_DEST='D://files/scripts/',
    UPLOADED_SCRIPTS_URL='http://localhost:5000/files/scripts/',

    UPLOAD_FOLDER='D:/files/scripts/',

    PYTHON_INTERPRETER_PATH='C:/Users/Admin/AppData/Local/Programs/Python/Python37/python.exe',
    GCC_COMPILER_PATH="C:/MinGW/bin/g++.exe"
)
