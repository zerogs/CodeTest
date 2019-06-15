config = dict(
    DEBUG= True,
    SECRET_KEY='c6bbe7faa2b688f5481234958f836eb7',
    PONY={
        'provider': 'postgres',
        'user': 'dpywpywfcverss',
        'password': '6a05849c65e69815a56b61bc8e8d48f04bdc78915b22ebbaa4ea64e8e88d42ad',
        'host': 'ec2-46-137-113-157.eu-west-1.compute.amazonaws.com:5432',
        'database': 'do8h3sfa965aj',
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
