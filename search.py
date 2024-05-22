import streamlit as st
import mysql.connector
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from config import DATABASE_CONFIG

def app():
    st.title("搜索房源")

    # Function to get database connection
    def get_db_connection():
        connection = mysql.connector.connect(**DATABASE_CONFIG)
        return connection

    # Function to execute read query
    def execute_read_query(query=None):
        # st.write(query)
        connection = get_db_connection()
        if query is None:
            # Adjust this default query as per your requirements
            query = """
            SELECT Unit.*, Building.building_name, Building.location
            FROM Unit
            JOIN Building ON Unit.building_id = Building.building_id
            """
        df = pd.read_sql(query, connection)
        connection.close()
        return df

    # Function to execute write query (update, delete)
    def execute_write_query(query):
        # st.write(query)
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        connection.close()

    def get_building_name():
        connection = get_db_connection()
        cursor = connection.cursor()
        building_name_options = ['All']
        # Check if the building exists
        cursor.execute("SELECT Building_name FROM Building")
        building_names = cursor.fetchall()
        for building_name in building_names:
            building_name_options.append(building_name[0])

        connection.close()
        return building_name_options
        
    with st.form("search_form"):
        col1, col2 = st.columns(2)

        with col1:
            # 第一列的字段
            building_name = st.selectbox("公寓名称", get_building_name())
            min_price = st.number_input("最低价格", min_value=0, step=1, format='%d')
            max_price = st.number_input("最高价格", min_value=0, step=1, format='%d')
            location_options = ["Any", "New Jersey", "Manhattan upper", "Manhattan mid", "Manhattan lower", "LIC", "Brooklyn"]
            location = st.multiselect("位置", options=location_options, default=["Any"])

        with col2:
            # 第二列的字段
            roomtype_options = ["Any", 'Studio', '1b1b', '2b2b', '2b1b', '3b2b', '3b3b','4b3b']
            roomtype = st.multiselect("户型", options=roomtype_options, default=["Any"])
            roomtype_subunit = st.multiselect("房型", options=["Any", "All",'bedroom1', 'bedroom2', 'bedroom3', 'living_room'], default=["Any"])
            movein_date = st.date_input("入住时间")
            if_time = st.checkbox('搜索时间',value = False)
            pet = st.checkbox("宠物友好", value=False)
            washer_dryer = st.checkbox("室内洗烘", value=False)
            on_market = st.checkbox("On Market", value=False)

        include_unit = st.checkbox('搜索unit',value=False)
        search_apt = st.form_submit_button("搜索")
        # search_building = st.form_submit_button("搜索公寓")

    # Handle Search
    if search_apt:
        st.session_state['include_building_only'] = False
        st.session_state['include_unit'] = False
        st.session_state['include_subunit'] = False

        include_building = building_name != "All"
        # include_unit = min_price!= 0 or max_price != 0 or washer_dryer == True or on_market == True or 
        include_subunit = roomtype_subunit != ["Any"]
        
        search_query = "SELECT"
        search_conditions = []
        join_conditions = ""

        if include_subunit:
            # Query to include Sub_Unit, Unit, and Building
            search_query += """ sub_unit.room_type AS 房间,
                                sub_unit.sub_rent_price AS 房间租金,
                                sub_unit.use_livingroom AS 客厅住人,
                                Unit.unit_number AS 单元号,
                                Unit.rent_price AS 租金,
                                Unit.floorplan AS 户型,
                                Unit.floorplan_image AS 户型图,
                                Unit.size AS 面积sqft,
                                Unit.concession AS 优惠政策,
                                Unit.direction AS 朝向,
                                Unit.unit_video AS 单元视频,
                                Unit.unit_description AS 单元描述,
                                Unit.broker_fee AS 中介费,
                                Unit.available_date AS Availability,
                                Unit.washer_dryer AS 室内洗烘,                                
                                Unit.on_market AS "On Market",
                                Building.building_name AS 公寓名称,
                                Building.location AS 区域,
                                Building.address AS 地址,
                                Building.city,
                                Building.state,
                                Building.zipcode,
                                Building.building_description AS 公寓描述,
                                Building.building_location_image AS 公寓位置图片,
                                Building.pet AS 宠物友好,
                                Building.application_material AS 申请材料,
                                Building.washer_dryer_image AS 公用洗烘设施图片,
                                Building.amenity_image AS 设施图片,
                                Building.guarantee_policy AS 担保政策,
                                Building.source AS 来源,
                                Building.website AS 公寓网站,
                                sub_unit.sub_unit_id FROM sub_unit """
            join_conditions += "JOIN Unit ON sub_unit.Unit_ID = Unit.unit_id JOIN Building ON Unit.building_id = Building.building_id "
            if 'All' in roomtype_subunit:
                roomtype_subunit = ['bedroom1', 'bedroom2', 'bedroom3', 'living_room']
            roomtype_conditions = ["sub_unit.room_type = '{}'".format(rt) for rt in roomtype_subunit]
            search_conditions.append("({})".format(" OR ".join(roomtype_conditions)))
            if movein_date and if_time:
                search_conditions.append(f"Unit.available_date <= '{movein_date}' AND Unit.movein_before >= '{movein_date}'")
        
            if on_market:
                search_conditions.append("Unit.on_market = 1")
                
            st.session_state['include_subunit'] = True
            st.write("房间:")
            
        elif include_unit:
            # Query to include Unit and Building
            search_query += """ Building.building_name AS 公寓名称,
                                Unit.unit_number AS 单元号,
                                Unit.rent_price AS 租金,
                                Unit.floorplan AS 户型,
                                Unit.floorplan_image AS 户型图,
                                Unit.unit_video AS 单元视频,
                                Unit.size AS 面积sqft,
                                Unit.broker_fee AS 中介费,
                                Unit.concession AS 优惠政策,
                                Unit.direction AS 朝向, 
                                Unit.unit_description AS 单元描述,
                                Unit.available_date AS Availability,
                                Unit.movein_before,
                                Unit.washer_dryer AS 室内洗烘,
                                Unit.on_market AS "On Market",
                                Building.location AS 区域,
                                Building.building_description AS 公寓描述,
                                Building.building_location_image AS 公寓位置图片,
                                Building.pet AS 宠物友好,
                                Building.application_material AS 申请材料,
                                Building.washer_dryer_image AS 公用洗烘设施图片,
                                Building.amenity_image AS 设施图片,
                                Building.guarantee_policy AS 担保政策,
                                Building.source AS 来源,
                                Building.website AS 公寓网站,
                                Unit.unit_id,
                                Building.building_id FROM Unit """
            join_conditions += "JOIN Building ON Unit.building_id = Building.building_id "
            if movein_date and if_time:
                search_conditions.append(f"Unit.available_date <= '{movein_date}' AND Unit.movein_before >= '{movein_date}'")

            if on_market:
                search_conditions.append("Unit.on_market = 1")
                
            st.write("单元:")
            st.session_state['include_unit'] = True
        else:
            # Query to include only Building
            search_query += """ Building.building_name AS 公寓名称,
                                Building.location AS 区域,
                                Building.address AS 地址,
                                Building.city,
                                Building.state,
                                Building.zipcode,
                                Building.building_description AS 公寓描述,
                                Building.building_location_image AS 公寓位置图片,
                                Building.pet AS 宠物友好,
                                Building.application_material AS 申请材料,
                                Building.washer_dryer_image AS 公用洗烘设施图片,
                                Building.amenity_image AS 设施图片,
                                Building.guarantee_policy AS 担保政策,
                                Building.source AS 来源,
                                Building.website AS 公寓网站,
                                Building.building_id FROM Building """
            st.write("公寓:")
            st.session_state['include_building_only'] = True
            
        if building_name != 'All':
            search_conditions.append(f"Building.Building_name LIKE '%{building_name}%'")
        if min_price and max_price:
            search_conditions.append(f"Unit.rent_price BETWEEN {min_price} AND {max_price}")
        if location != ['Any']:
            location_conditions = ["Building.location LIKE '%{}%'".format(loc) for loc in location]
            search_conditions.append("({})".format(" OR ".join(location_conditions)))
        if washer_dryer:
            search_conditions.append("Unit.washer_dryer = 1")
        if pet:
            pet_val = 1
            search_conditions.append(f"Building.pet = {pet_val}")
            
        if "Any" not in roomtype:
            roomtype_conditions = ["Unit.floorplan LIKE '%{}%'".format(loc) for loc in roomtype]
            search_conditions.append("({})".format(" OR ".join(roomtype_conditions)))


        final_query = search_query + join_conditions
        if search_conditions:
            final_query += "WHERE " + " AND ".join(search_conditions)

        df = execute_read_query(final_query)
        st.session_state['search_results'] = df

    # Display Search Results
    if 'search_results' in st.session_state:
        df = st.session_state['search_results']

        # Set up AgGrid options for editable grid
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True, minWidth=150)
        gb.configure_selection('multiple', use_checkbox=True)
        grid_options = gb.build()

        # Display the grid
        grid_response = AgGrid(
            df, 
            gridOptions=grid_options,
            height=600, 
            width='100%',
            data_return_mode='AS_INPUT', 
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True
        )

        if 'data' in grid_response:
            updated_df = grid_response['data']
            if not updated_df.equals(df):
                if st.button('更新'):
                    is_building_only = st.session_state.get('include_building_only', False)
                    is_unit_included = st.session_state.get('include_unit', False)
                    is_subunit_included = st.session_state.get('include_subunit', False)
                    # st.write(is_building_only,is_building_only,is_subunit_included)
                    
                    building_column_name_mapping = {
                        '公寓名称': 'building_name',
                        '区域': 'location',
                        '地址': 'address',
                        'city': 'city',
                        'state': 'state',
                        'zipcode': 'zipcode',
                        '公寓描述': 'building_description',
                        '公寓位置图片': 'building_location_image',
                        '宠物友好': 'pet',
                        '申请材料': 'application_material',
                        '公用洗烘设施图片': 'washer_dryer_image',
                        '设施图片': 'amenity_image',
                        '担保政策': 'guarantee_policy',
                        '来源': 'source',
                        '公寓网站': 'website',
                        'movein_range':'movein_range'
                    }

                    
                    unit_column_name_mapping = {
                        '单元号': 'unit_number',
                        '租金': 'rent_price',
                        '户型': 'floorplan',
                        '户型图': 'floorplan_image',
                        '面积sqft': 'size',
                        '优惠政策': 'concession',
                        '朝向': 'direction',
                        '单元视频': 'unit_video',
                        '单元描述': 'unit_description',
                        '中介费': 'broker_fee',
                        'Availability': 'available_date',
                        '室内洗烘': 'washer_dryer',
                        'On Market':'on_market'
                    }

                    sub_unit_column_name_mapping = {
                        '房间': 'room_type',
                        '房间租金': 'sub_rent_price',
                        '客厅住人': 'use_livingroom',
                        '兴趣点ID': 'interest_pp_id'
                    }
                 
                    # Handle updates for Building, Unit, and Sub_Unit
                    for i in updated_df.index:
                        if is_subunit_included:
                            # Construct and execute UPDATE query for Sub_Unit
                            sub_unit_update_query = "UPDATE sub_unit SET "
                            sub_unit_update_query += ", ".join([f"{sub_unit_column_name_mapping[col]} = '{updated_df.at[i, col]}'" for col in updated_df.columns if col in sub_unit_column_name_mapping])
                            sub_unit_update_query += f" WHERE sub_unit_id = {updated_df.at[i, 'sub_unit_id']}"
                            execute_write_query(sub_unit_update_query)
    
                        elif is_unit_included:
                            # Construct and execute UPDATE query for Unit
                            unit_update_query = "UPDATE Unit SET "
                            unit_update_query += ", ".join([f"{unit_column_name_mapping[col]} = '{updated_df.at[i, col]}'" for col in updated_df.columns if col in unit_column_name_mapping])
                            unit_update_query += f" WHERE unit_id = {updated_df.at[i, 'unit_id']}"
                            execute_write_query(unit_update_query)
    
                        else:
                            # Construct and execute UPDATE query for Building
                            building_update_query = "UPDATE Building SET "
                            building_update_query += ", ".join([f"{building_column_name_mapping[col]} = '{updated_df.at[i, col]}'" for col in updated_df.columns if col in building_column_name_mapping])
                            building_update_query += f" WHERE building_id = {updated_df.at[i, 'building_id']}"
                            execute_write_query(building_update_query)
                        
                    st.success("更新成功！")

        
        # Store selected rows for deletion
        selected = grid_response['selected_rows']
        if selected:
            st.session_state['selected_for_deletion'] = selected
            #st.write("Selected rows:", selected)
            
            if st.button('删除'):
                is_building_only = st.session_state.get('include_building_only', False)
                is_unit_included = st.session_state.get('include_unit', False)
                is_subunit_included = st.session_state.get('include_subunit', False)
                for row in st.session_state['selected_for_deletion']:
                    if is_subunit_included:
                        # DELETE FROM Sub_Unit WHERE sub_unit_id = value
                        sub_unit_delete_query = f"DELETE FROM sub_unit WHERE sub_unit_id = {row['sub_unit_id']}"
                        execute_write_query(sub_unit_delete_query)

                    elif is_unit_included:
                        # DELETE FROM Unit WHERE unit_id = value
                        unit_delete_query = f"DELETE FROM Unit WHERE unit_id = {row['unit_id']}"
                        execute_write_query(unit_delete_query)

                    else:
                        # DELETE FROM Building WHERE building_id = value
                        building_delete_query = f"DELETE FROM Building WHERE building_id = {row['building_id']}"
                        execute_write_query(building_delete_query)
                
                st.success("删除成功！")


       

if __name__ == "__main__":
    app()
