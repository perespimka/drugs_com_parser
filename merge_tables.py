from sshtunnel import SSHTunnelForwarder
import pymysql
import sqlite3
import logging
from my_utils import base_logger
import traceback

logger = base_logger('merge_tables.log')

def medicines_new_fill(mysql_connection, ndrugs_data, my_id):
    MEDICINES_NDRUGS_FIELDS = {'Therapeutic_indications': ('indications', 'what_is'), 
                        'Dosage_Posology': ('dosage', ), 
                        'Contraindications': ('contraindications',), 
                        'Special_warnings_and_precautions_for_use': ('how_should_i_use', 'uses_of_in_details'),
                        'Interaction': ('interactions',),
                        'Undesirable_effects': ('side_effects',), 
                        'Overdose': ('overdose',), 
                        'description': ('description',), 
                        'ingredient_matches': ('active_ingredient_matches',), 
                        'list_of_subs': ('list_of_substitutes',)
    }
    MEDICINES_FIELDS = ['Therapeutic_indications', 'Dosage_Posology', 'Contraindications', 'Special_warnings_and_precautions_for_use', 
                       'Interaction', 'Undesirable_effects', 'Overdose', 'description', 'ingredient_matches', 'list_of_subs'
    ]
    with mysql_connection.cursor() as my_cursor:
        fields = ','.join(MEDICINES_FIELDS)
        query = f'SELECT {fields} FROM medicines_new WHERE id=%s;'
        my_cursor.execute(query, (my_id,))
        rxlist_data = my_cursor.fetchone()
    for i, field in enumerate(rxlist_data):
        #Если поле в таблице rxlist отсутствует, заменим его соответствующими значениями из ndrugs
        if not field:
            ndrugs_total_value = ''
            key = MEDICINES_FIELDS[i]
            ndrugs_keys = MEDICINES_NDRUGS_FIELDS[key]
            for ndrugs_key in ndrugs_keys:
                ndrugs_total_value += ndrugs_data[ndrugs_key]
            with mysql_connection.cursor() as my_cursor:
                query = f'UPDATE medicines_new SET {key}=%s WHERE id=%s;'
                my_cursor.execute(query, (ndrugs_total_value, my_id))
                mysql_connection.commit()
    logger.info(f'{ndrugs_data["name"]} объединен с аналогом из medicines_new')
            

            


def main():
    HOST = '5.252.192.198'

    lite_connection = sqlite3.connect('parser.db')
    lite_connection.row_factory = sqlite3.Row
    with SSHTunnelForwarder(
        (HOST, 22),
        ssh_username = 'root',
        ssh_password = 'HcJ5x6CV',
        remote_bind_address = ('127.0.0.1', 3306),
        local_bind_address = ('127.0.0.1', 3306)

    ) as server:
        mysql_connection = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='pillintrip',
            password='33Kgtsl11',
            db='prod_pillintrip_com',
            charset='utf8mb4'
        )


        for i in range(2, 33364):   #(2,33364)
            lite_cursor = lite_connection.cursor()

            try:
                query = 'SELECT * FROM ndrugs WHERE rowid=?'
                lite_cursor.execute(query, (i,))
                ndrugs_data = lite_cursor.fetchone()


                with mysql_connection.cursor() as my_cursor:
                    query = 'SELECT id FROM medicines_new WHERE Drug_name=%s;'
                    my_cursor.execute(query, (ndrugs_data['name'],))
                    my_id = my_cursor.fetchone()
                if my_id:
                    medicines_new_fill(mysql_connection, ndrugs_data, my_id[0])

                else:
                    logger.debug(f'Insert {ndrugs_data["name"]}')
                    print(f'Insert {ndrugs_data["name"]}')
                    with mysql_connection.cursor() as my_cursor:
                        query = '''
                                    INSERT INTO medicines_new (Drug_name,  Therapeutic_indications, Dosage_Posology, 
                                    Contraindications, Special_warnings_and_precautions_for_use, Interaction,
                                    Undesirable_effects, Overdose, description, ingredient_matches, list_of_subs) 
                                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                        '''
                        my_cursor.execute(query, (
                            ndrugs_data['name'], ndrugs_data['indications'] + ndrugs_data['what_is'], ndrugs_data['dosage'],
                            ndrugs_data['contraindications'], ndrugs_data['how_should_i_use'] + ndrugs_data['uses_of_in_details'], 
                            ndrugs_data['interactions'], ndrugs_data['side_effects'], ndrugs_data['overdose'], 
                            ndrugs_data['description'], ndrugs_data['active_ingredient_matches'], ndrugs_data['list_of_substitutes']
                        ))
                        mysql_connection.commit()
            except Exception as e:
                print(f'ERROR: {e}')
                logger.warning(f'ERROR: {e}')
                print(traceback.format_exc())


            finally:
                lite_cursor.close()
                mysql_connection.close()
                lite_connection.close()



if __name__ == "__main__":
    main()