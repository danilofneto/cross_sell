import pickle
import inflection
import pandas as pd

class HealthInsurance( object ):
    
    def __init__( self ):
        self.home_path                   = 'parameter'
        self.annual_premium_scaler       = pickle.load( open( self.home_path + '/annual_premium_scaler.pkl', 'rb' ) )
        self.age_scaler                  = pickle.load( open( self.home_path + '/age_scaler.pkl', 'rb' ) )
        self.vintage_scaler              = pickle.load( open( self.home_path + '/vintage_scaler.pkl', 'rb' ) )
        self.premium_per_day_scaler      = pickle.load( open( self.home_path + '/premium_per_day_scaler.pkl', 'rb' ) )
        self.gender_scaler               = pickle.load( open( self.home_path + '/gender_scaler.pkl', 'rb' ) )
        self.region_code_scaler          = pickle.load( open( self.home_path + '/region_code_scaler.pkl', 'rb' ) )
        self.policy_sales_channel_scaler = pickle.load( open( self.home_path + '/policy_sales_channel_scaler.pkl', 'rb' ) )
        
        
        
    def data_cleaning( self, df1 ):  

        ## 1.1 Rename Columns

        old_columns = ['id', 'Gender', 'Age', 'Driving_License', 'Region_Code',
               'Previously_Insured', 'Vehicle_Age', 'Vehicle_Damage', 'Annual_Premium',
               'Policy_Sales_Channel', 'Vintage']

        snakecase = lambda x: inflection.underscore( x )

        new_columns = list( map( snakecase, old_columns ) )

        # rename
        df1.columns = new_columns
        
        return df1
    
    def feature_engineering( self, df2 ):
        ## 2.2 Feature Engineering

        # Create risk age variable
        df2['risk_age'] = df2['age'].apply( lambda x: 'Yes' if x < 25 else 'No' )

        # Vintage_month
        # Separating vintage in months
        df2['vintage_month'] = df2['vintage'].apply( lambda x: 'month' if  x <= 31 else 'quarter' if (x > 31 ) & (x <= 90) else 
                                                    'semester' if (x > 90) & (x <= 180) else 'close to a year')
        # premium_per_day (annual_premium/vintage)
        df2['premium_per_day'] = round( df2['annual_premium'] / df2['vintage'], 2 )
        

        df2['vehicle_damage'] = df2['vehicle_damage'].apply( lambda x: 1 if x == 'Yes' else 0 )

        return df2
       
    
    def data_preparation( self, df5 ):
        # 5.0 DATA PREPARATION

        ## 5.1 Standardization
        # annual_premium
        df5['annual_premium'] = self.annual_premium_scaler.fit_transform( df5[['annual_premium']].values )

        ## 5.2 Rescalling

        # age - MinMaxScaler
        df5['age'] = self.age_scaler.fit_transform( df5[['age']].values )
        

        # vintage - MinMaxScaler
        df5['vintage'] = self.vintage_scaler.fit_transform( df5[['vintage']].values )
       
        # premium_per_day - RobustScaler
        df5['premium_per_day'] = self.premium_per_day_scaler.fit_transform( df5[['premium_per_day']].values )        

        ## 5.3 Encoder

        # gender - Target Encoding
        
        df5.loc[:, 'gender'] = df5['gender'].map( self.gender_scaler )      


        # vehicle_age - One Hot Encoding
        df5 = pd.get_dummies( df5, prefix='vehicle_age', columns=['vehicle_age'] )

        # region_code - Target Encoding / Frequency Encoding
        
        df5.loc[:, 'region_code'] = df5['region_code'].map( self.region_code_scaler )       


        # policy_sales_channel - Frequency Encoding
         
        df5.loc[:, 'policy_sales_channel'] = df5['policy_sales_channel'].map( self.policy_sales_channel_scaler )        

        # vintage_month 
        vm_dict = {'month': 1, 'quarter': 2, 'semester': 3, 'close to a year': 4}
        df5['vintage_month'] = df5['vintage_month'].map( vm_dict )
                
        cols_selected = [ 'premium_per_day', 'vintage', 'annual_premium', 'age', 'region_code', 'vehicle_damage', 'policy_sales_channel', 'previously_insured' ]
        
        return df5[ cols_selected ]


    def get_prediction (self, model, original_data, test_data):
        
        # prediction
        pred = model.predict_proba(test_data)

        # join pred into original data
        original_data['score'] = pred[:,1].tolist()
        
        return original_data.to_json(orient = 'records', date_format = 'iso')
