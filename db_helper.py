import mysql.connector as mariadb
import datetime
from influxdb import InfluxDBClient
import tzlocal

####### TO_DO ########

# change select statement to get most recent record
# select top 1/limit 1
# order by DESC

class db_helper():
    def __init__(self):
        self.db_host = '192.168.0.10'
        self.db_host_port = '3306'
        self.influx_port = '8086'
        self.db_user = 'rpi'
        self.db_pass = 'warm_me'
        self.db = 'temp_logger'
        self.local_timezone = tzlocal.get_localzone()

    def db_data(self, n_variables, statement, default):

        con = mariadb.connect(host=self.db_host, port=self.db_host_port, user=self.db_user,
                              password=self.db_pass, database=self.db)
        cur = con.cursor()

        cur.execute(statement)

        if n_variables == 1:
            output = default

            for row in cur:
                output = row[0]
            
            return output

        elif n_variables > 1:
            output = [default] * n_variables

            for row in cur:
                output = row

            return output
    
    def insert_db_data(self, statement):

        con = mariadb.connect(host=self.db_host, port=self.db_host_port, user=self.db_user,
                              password=self.db_pass, database=self.db)
        cur = con.cursor()

        try:
            cur.execute(statement)
            con.commit()
        except:
            con.rollback()
        con.close()

        return

    def get_inside_temp(self):
### new - influx
        client = InfluxDBClient(host=self.db_host, port=self.influx_port)

        client.switch_database('home')

        statement = """
                    select CurrentTemp as temp 
                    from sensor
                    where "sensor_measurements" = 'home/inside/sensor/CurrentTemp' 
                    order by time DESC
                    limit 1
                    """

        response = client.query(statement)

        temps = next(iter(response))

        return temps[0]['temp']

#### old

    #     n_variables = 1
    #     statement = """
    #                     SELECT
    #                     avg(temp)
    #                     FROM temperature 
    #                     WHERE ts > DATE_SUB(now(), INTERVAL 90 second)
    #                     ORDER BY ts ASC
    #                     """
    #     default = 99

    #     return self.db_data(n_variables = n_variables, statement = statement, default = default)

    def get_outside_temp(self):
### new - influx
        client = InfluxDBClient(host=self.db_host, port=self.influx_port)

        client.switch_database('home')

        statement = """
                    select temperature,
                    feels_like 
                    from sensor
                    where "sensor_measurements" = 'home/outside/sensor' 
                    order by time DESC
                    limit 1
                    """

        response = client.query(statement)

        temps = next(iter(response))
        
        return temps[0]


#### old

        # n_variables = 2
        # statement = """
        #             select temperature, 
        #             feels_like
        #             from sensor
        #             where feels_like > 0
        #             order by time desc
        #             limit 1
        #             """
        # default = 99

        # return self.db_data(n_variables=n_variables, statement=statement, default=default)



    def get_control_settings(self):
        n_variables = 2
        statement = """
                    SELECT
                    temp_setting,
                    power
                    FROM heater_controls 
                    ORDER BY ts DESC
                    limit 1
                    """

        default = 0

        return self.db_data(n_variables = n_variables, statement = statement, default = default)

    def get_heat_indicator(self):
### new - influx
        client = InfluxDBClient(host=self.db_host, port=self.influx_port)

        client.switch_database('home')

        statement = """
                    select heater_running
                    from controls
                    where "control_parameter" = 'home/inside/control/heater_running' 
                    order by time DESC
                    limit 1
                    """

        response = client.query(statement)

        ind = next(iter(response))
        
        return ind[0]['heater_running']


#### old
        # n_variables = 1
        # statement = """
        #             SELECT
        #             heater_on
        #             FROM heater_log
        #             ORDER BY ts DESC
        #             limit 1
        #             """
        # default = 0

        # return self.db_data(n_variables = n_variables, statement = statement, default = default)

    def insert_control_settings(self, temperature, power):
        statement = """
                    INSERT into heater_controls
                    (temp_setting,
                    power)
                    VALUES
                    ({},{})""".format(temperature, power)
        
        self.insert_db_data(statement)

        return

    def get_temps(self):
        client = InfluxDBClient(host=self.db_host, port=self.influx_port)

        client.switch_database('home')

        statement1 = """
                    select mean(temperature) as temp 
                    into temp
                    from sensor 
                    where "location" = 'lounge' 
                    and time > now() - 4h
                    group by time(1m)
                    tz('Australia/Melbourne')
                    """

        statement2 = """
                    select temperature as air_temp, feels_like
                    into temp
                    from sensor 
                    where "location" = 'outside'
                    and time > now() - 4h
                    tz('Australia/Melbourne')

                    """

        statement3 = """
                    select *
                    from temp
                    where time > now() - 4h
                    tz('Australia/Melbourne')
                    """

        client.query(statement1+";"+statement2)

        response = client.query(statement3, epoch='s')

        temps = next(iter(response))
        
        for temp in temps:
            temp['time'] = datetime.datetime.fromtimestamp(temp['time'])

        return temps



    def get_outside_temps(self):
        statement = """
                SELECT
                UNIX_TIMESTAMP(ts) as time,
                air_temp,
                apparent_t as feels_like
                FROM outside_conditions
                where ts > DATE_SUB(now(), INTERVAL 12 hour)
                ORDER BY ts ASC
                """

        con = mariadb.connect(host=self.db_host, port=self.db_host_port, user=self.db_user,
                            password=self.db_pass, database=self.db)
        cur = con.cursor()

        cur.execute(statement)

        outside = []
        for row in cur:
            unix_timestamp = row[0]
            local_time = datetime.datetime.fromtimestamp(
                unix_timestamp, self.local_timezone)

            outs = {
                'ts': local_time,
                'air_temp': row[1],
                'feels_like': row[2]}
            outside.append(outs)
        return outside

