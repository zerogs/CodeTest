config = dict(
    DEBUG= True,
    SECRET_KEY='c6bbe7faa2b688f5481234958f836eb7',
    PONY={
        'provider': 'postgres',
        'user': 'postgres',
        'password': 'thrashtilldeath1983',
        'host': 'localhost',
        'database': 'dproject',
    },
    MAX_CONTENT_SIZE = 16384,
    UPLOADS_DEFAULT_DEST='/home/izhitnikov/files/default/',
    UPLOADS_DEFAULT_URL ='http://localhost:5000/files/default/',

    UPLOADED_DATA_DEST='/home/izhitnikov/files/group_lists/',
    UPLOADED_DATA_URL='http://localhost:5000/files/group_lists/',

    UPLOADED_SCRIPTS_DEST='/home/izhitnikov/ffiles/scripts/',
    UPLOADED_SCRIPTS_URL='http://localhost:5000/files/scripts/',

    UPLOAD_FOLDER='/home/izhitnikov/files/scripts/',

    PYTHON_INTERPRETER_PATH='python3',
    GCC_COMPILER_PATH="C:/MinGW/bin/g++.exe"
)
