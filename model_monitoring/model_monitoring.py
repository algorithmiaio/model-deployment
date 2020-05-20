import Algorithmia
import semantic_version
import mysql.connector
import pandas as pd
import random
import time
import json
from mysql.connector import errorcode
from dbrequests import Database
from datetime import date

algo_name = 'username/algoname'

experiment_count = 1000 # Number of samples that needs to be collected to run an experiment
experiment_threshold = 2 # An algorithm request shouldn't take more than 2 seconds on average
experiment_split = 0.5 # Call experimental model 50% of the time
check_db_init = False

db_name = 'ModelMonitoring'
db_username = 'db_username'
db_password = 'db_password'
db_host = 'XXX.us-east-1.rds.amazonaws.com'

creds = {
    "user": db_username,
    "password": db_password,
    "host": db_host,
    "db": db_name
}

db_tables = {}
db_tables['versions'] = (
    "CREATE TABLE `versions` ("
    "  `ver_no` int(11) NOT NULL AUTO_INCREMENT,"
    "  `version` varchar(65535) NOT NULL,"
    "  `status` ENUM('success', 'fail', 'experiment') NOT NULL,"
    "  `date` date NOT NULL,"
    "  PRIMARY KEY (`ver_no`)"
    ") ENGINE=InnoDB"
)

db_tables['metaData']= (
    "CREATE TABLE `metaData` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `setting` varchar(65535) NOT NULL,"
    "  `val` varchar(65535),"
    "  PRIMARY KEY (`id`)"
    ") ENGINE=InnoDB"
)

db_tables['experiments'] = (
"CREATE TABLE `experiments` ("
    "  `experiment_no` int(11) NOT NULL AUTO_INCREMENT,"
    "  `prev_ver` varchar(65535) NOT NULL,"
    "  `next_ver` varchar(65535) NOT NULL,"
    "  `start_date` date,"
    "  `end_date` date,"
    "  `promoted` BOOL,"
    "  PRIMARY KEY (`experiment_no`)"
    ") ENGINE=InnoDB"
)

db_tables['experimentData'] = (
"CREATE TABLE `experimentData` ("
    "  `request_no` int(11) NOT NULL AUTO_INCREMENT,"
    "  `data` varchar(65535) NOT NULL,"
    "  `date` date NOT NULL,"
    "  `algo_version` varchar(65535) NOT NULL,"
    "  `experiment_no` int(11) NOT NULL,"
    "  PRIMARY KEY (`request_no`),"
    "  FOREIGN KEY (`experiment_no`) REFERENCES experiments(experiment_no)"
    "  ON DELETE CASCADE"
    ") ENGINE=InnoDB"
)

client = Algorithmia.client("simXXXXXXXX")

def get_latest_algo_version():
    '''
    Returns the latest semantic algo version if available
    '''
    # Get all published versions
    r = client.algo(algo_name).versions(published=True)
    # Extract only versions
    all_versions = list(map(lambda x: semantic_version.Version(x['version_info']['semantic_version']), r.results))
    # Get the latest version
    if len(all_versions) > 0:
        latest_version = max(all_versions)
        return latest_version
    else:
        return None

def get_db_stable_version():
    '''
    Returns the semantic DB stable version
    '''
    db = Database(creds=creds)
    df = db.send_query("""SELECT * FROM ModelMonitoring.metaData WHERE setting = 'stable_version';""")
    db.close()
    db_stable_version = df.loc[0]['val']
    if db_stable_version:
        return semantic_version.Version(db_stable_version)
    else:
        return

def get_db_exp_version():
    '''
    Returns the semantic DB experiment version
    '''
    db = Database(creds=creds)
    df = db.send_query("""SELECT * FROM ModelMonitoring.metaData WHERE setting = 'experiment_version';""")
    db.close()
    db_exp_version = df.loc[0]['val']
    if db_exp_version:
        return semantic_version.Version(db_exp_version)
    else:
        return

def get_db_exp_data_count(experiment_no):
    '''
    Count number of registered data points in DB
    '''
    db = Database(creds=creds)
    df = db.send_query("""SELECT * FROM ModelMonitoring.experimentData WHERE experiment_no = '{}';""".format(experiment_no))
    db.close()
    return len(df)

def get_exp_no():
    '''
    Get current running experiment id/number
    '''
    db = Database(creds=creds)
    df = db.send_query("""SELECT MAX(experiment_no) FROM ModelMonitoring.experiments;""")
    experiment_no = int(df["MAX(experiment_no)"])
    return experiment_no

def is_experiment_running():
    '''
    Checks if an experiment is already running
    '''
    db = Database(creds=creds)
    df = db.send_query("""SELECT * FROM ModelMonitoring.metaData WHERE setting = 'experiment_running';""")
    db.close()
    exp_running = db_stable_version = df.loc[0]['val']
    if exp_running == "True":
        return True
    elif exp_running == "False":
        return False
    else:
        raise Exception("Something has gone wrong!")

def get_test_version():
    '''
    Split all incoming requests according to (experiment_split)
        and return the corresponding semantic version
    '''
    choice = random.random()
    sign = ">=" if choice >= experiment_split else "<"
    print("Picking random split: {:10.3f}{}{}".format(choice, sign, experiment_split))
    if choice >= experiment_split:
        # Get the experimental version
        response = ("experiment", get_db_exp_version())
    else:
        # Get the stable version
        response = ("stable", get_db_stable_version())
    return response

def register_test_data(algo_exp_data, test_version):
    '''
    Register the test/experimental call
    '''
    today_date = date.today()
    experiment_no = get_exp_no()
    experiment_data = pd.DataFrame([[json.dumps(algo_exp_data), today_date, str(test_version), experiment_no]],
                                   columns=["data", "date", "algo_version", "experiment_no"])
    db = Database(creds=creds)
    db.send_data(experiment_data, 'experimentData', mode='insert')
    db.close()

def resolve_experiment(experiment_no):
    '''
    Resolve the running experiment
    '''
    # See if the experiment version can be promoted
    # Promote or fail experiment version
    # Update experiment in experiments table
    # Update version info in versions table
    # Update metadata with new stable version if promoted
    stable_version = str(get_db_stable_version())
    experiment_version = str(get_db_exp_version())
    # Collect all experiment data
    db = Database(creds=creds)
    df_stable_stable_data = db.send_query(
        """SELECT * FROM ModelMonitoring.experimentData WHERE algo_version = '{}' AND experiment_no = '{}';""".format(
            stable_version, experiment_no
        )
    )
    df_stable_experiment_data = db.send_query(
        """SELECT * FROM ModelMonitoring.experimentData WHERE algo_version = '{}' AND experiment_no = '{}';""".format(
            experiment_version, experiment_no
        )
    )
    stable_avg_runtime = None
    experiment_avg_runtime = None
    # Let's still record the stable statistics just in case we use them.
    if not df_stable_stable_data.empty:
        stable_all_times = list(map(lambda x: json.loads(x)["algo_timing"], df_stable_stable_data["data"]))
        stable_avg_runtime = sum(stable_all_times)/len(stable_all_times)
    else:
        stable_all_times = -1
        stable_avg_runtime = -1
    if not df_stable_experiment_data.empty:
        experiment_all_times = list(map(lambda x: json.loads(x)["algo_timing"], df_stable_stable_data["data"]))
        experiment_avg_runtime = sum(experiment_all_times)/len(experiment_all_times)
    else:
        experiment_all_times = -1
        experiment_avg_runtime = -1

    # If no data was collected for the experimental model, abort deployment, and fail the deployment
    if experiment_avg_runtime < 0:
        fail_experiment_version(experiment_version, experiment_no)
    else:
        # Otherwise, assess if the average runtime is not worse than experiment_threshold
        print("Average runtime for experiment model: {}".format(experiment_avg_runtime))
        if experiment_avg_runtime > experiment_threshold:
            fail_experiment_version(experiment_version, experiment_no)
        else:
            promote_experiment_version(experiment_version, experiment_no)


def promote_experiment_version(version_update, experiment_number):
    print("Promoting version {}...".format(version_update))
    db = Database(creds=creds)
    today_date = date.today()

    experiment_running = pd.DataFrame([[1, "experiment_running", "False"]], columns=["id", "setting", "val"])
    stable_version = pd.DataFrame([[3, "stable_version", version_update]], columns=["id", "setting", "val"])
    experiment_version = pd.DataFrame([[4, "experiment_version", None]], columns=["id", "setting", "val"])

    db.send_data(experiment_running, 'metaData', mode='update')
    db.send_data(stable_version, 'metaData', mode='update')
    db.send_data(experiment_version, 'metaData', mode='update')

    experiment_itself = pd.DataFrame([[experiment_number, today_date, True]], columns=["experiment_no", "end_date", "promoted"])
    db.send_data(experiment_itself, 'experiments', mode='update')

    version_id = int(db.send_query("""SELECT * FROM ModelMonitoring.versions WHERE version = '{}';""".format(version_update))['ver_no'].iloc[-1])

    version = pd.DataFrame([[version_id, version_update, "success"]], columns=["ver_no","version", "status"])
    db.send_data(version, 'versions', mode='update')
    print("Version {} has been promoted!".format(version_update))

def fail_experiment_version(version_update, experiment_number):
    print("Failing version {}...".format(version_update))
    db = Database(creds=creds)
    today_date = date.today()

    experiment_running = pd.DataFrame([[1, "experiment_running", "False"]], columns=["id", "setting", "val"])
    experiment_version = pd.DataFrame([[4, "experiment_version", None]], columns=["id", "setting", "val"])

    db.send_data(experiment_running, 'metaData', mode='update')
    db.send_data(experiment_version, 'metaData', mode='update')

    experiment_itself = pd.DataFrame([[experiment_number, today_date, False]], columns=["experiment_no", "end_date", "promoted"])
    db.send_data(experiment_itself, 'experiments', mode='update')

    version_id = int(db.send_query("""SELECT * FROM ModelMonitoring.versions WHERE version = '{}';""".format(version_update))['ver_no'].iloc[-1])

    version = pd.DataFrame([[version_id, version_update, "fail"]], columns=["ver_no","version", "status"])
    db.send_data(version, 'versions', mode='update')
    print("Version {} has been failed!".format(version_update))

def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))

def get_db_obj():
    '''
    Get the DB cursor object.
    '''
    cnx = mysql.connector.connect(user=db_username, password=db_password, host=db_host)
    cursor = cnx.cursor(buffered=True)
    return cursor, cnx

def init_database():
    '''
    Create all the tables we're going to use, and the meta data if it doesn't exist.
    '''
    global check_db_init
    curr, conn = get_db_obj()
    # First, create database if it doesn't exist
    try:
        curr.execute("USE {}".format(db_name))
    except mysql.connector.Error as err:
        print("Database {} does not exists.".format(db_name))
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(curr)
            print("Database {} created successfully.".format(db_name))
            conn.database = db_name
        else:
            print(err)
        # Second, create all tables that are going to be used
        for table_name in db_tables:
            table_description = db_tables[table_name]
            try:
                print("Creating table {}: ".format(table_name), end='')
                curr.execute(table_description)
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("already exists.")
                else:
                    print(err.msg)
            else:
                print("OK")
        print("Inserting metadata")
        experiment_running = pd.DataFrame([[1, "experiment_running", "False"]], columns=["id", "setting", "val"])
        experiment_count = pd.DataFrame([[2, "experiment_count", None]], columns=["id", "setting", "val"])
        stable_version = pd.DataFrame([[3, "stable_version", None]], columns=["id", "setting", "val"])
        experiment_version = pd.DataFrame([[4, "experiment_version", None]], columns=["id", "setting", "val"])
        db = Database(creds=creds)
        db.send_data(experiment_running, 'metaData', mode='insert')
        db.send_data(experiment_count, 'metaData', mode='insert')
        db.send_data(stable_version, 'metaData', mode='insert')
        db.send_data(experiment_version, 'metaData', mode='insert')
        db.close()
        print("Metadata created successfully")
    check_db_init = True
    return

def call_algorithm(input):
    # If there isn't a "latest-stable-version" yet, update it to the latest algorithm version.
    db_stable_version = get_db_stable_version()
    print("DB stable version is: {}".format(db_stable_version))
    if not db_stable_version:
        latest_algo_version = get_latest_algo_version()
        if not latest_algo_version:
            raise Exception("There isn't a published version of the model {} yet.".format(algo_name))
        latest_stable_version = pd.DataFrame([[3, "stable_version", str(latest_algo_version)]],
                                             columns=["id", "setting", "val"])
        today_date = date.today()
        exp_start_date = today_date
        exp_end_date = today_date
        initial_experiment = pd.DataFrame([["None", str(latest_algo_version), exp_start_date, exp_end_date, True]],
                                          columns=["prev_ver", "next_ver", "start_date", "end_date", "promoted"])
        init_version = pd.DataFrame([[str(latest_algo_version), "success", today_date]],
                                    columns=["version", "status", "date"])
        db = Database(creds=creds)
        db.send_data(latest_stable_version, 'metaData', mode='update')
        db.send_data(initial_experiment, 'experiments', mode='insert')
        db.send_data(init_version, 'versions', mode='insert')
        db.close()
        print("First stable version set to: {}".format(latest_algo_version))
    # Get latest published version from Algorithmia
    latest_algo_version = get_latest_algo_version()
    # Get stable version from DB
    db_stable_version = get_db_stable_version()
    # If there isn't a new deployed version, just called the DB stable version
    if not latest_algo_version > db_stable_version:
        print("Calling the stable version: {}".format(latest_algo_version))
        return client.algo("{}/{}".format(algo_name, str(latest_algo_version))).pipe(input)
    else:
        print("New deployed version has been found: {}".format(latest_algo_version))
        # Create a new experiment if it isn't already running
        if not is_experiment_running():
            print("Starting new experiment")
            # Start new experiment
            today_date = date.today()
            new_version = pd.DataFrame([[str(latest_algo_version), "experiment", today_date]],
                                       columns=["version", "status", "date"])
            new_experiment = pd.DataFrame([[str(db_stable_version), str(latest_algo_version), today_date, None, None]],
                                              columns=["prev_ver", "next_ver", "start_date", "end_date", "promoted"])
            experiment_running = pd.DataFrame([[1, "experiment_running", "True"]],
                                              columns=["id", "setting", "val"])
            experiment_version = pd.DataFrame([[4, "experiment_version", str(latest_algo_version)]],
                                              columns=["id", "setting", "val"])
            db = Database(creds=creds)
            db.send_data(new_version, 'versions', mode='insert')
            db.send_data(new_experiment, 'experiments', mode='insert')
            db.send_data(experiment_running, 'metaData', mode='update')
            db.send_data(experiment_version, 'metaData', mode='update')
            db.close()
        else:
            print("Continuing existing experiment")
        # Get test version
        test_type, test_version = get_test_version()
        algo_start = time.time()
        # Make a call to the testing (either stable or experiment) endpoint
        print("Calling type: {}, version: {}".format(test_type, test_version))
        algo_response = client.algo("{}/{}".format(algo_name, str(test_version))).pipe(input)
        algo_end = time.time()
        # Calculate total timing for algorithm call
        algo_timing = algo_end-algo_start
        algo_exp_data = {"algo_timing": algo_timing}
        print("Algorithm timing: {}".format(algo_timing))
        # Register test data into DB
        register_test_data(algo_exp_data, test_version)
        # Get total number of experimental calls that have been made
        experiment_no = get_exp_no()
        db_exp_count = get_db_exp_data_count(experiment_no)
        print("Number of test (stable + experiment) calls made: {}".format(db_exp_count))
        # After call is made, check if the experiment can be ended
        if db_exp_count >= experiment_count:
            print("Resolving experiment")
            resolve_experiment(experiment_no)
        # At last, return the algorithm response
        return algo_response

def apply(input):
    # Check if DB has been initialized for this algorithm slot
    if not check_db_init:
        init_database()
    r = call_algorithm(input)
    return r.result
