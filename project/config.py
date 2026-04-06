import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'smart-crop-planning-secret-key-2024'
    DATABASE = os.path.join(BASE_DIR, 'crop_planning.db')
    MODEL_PATH = os.path.join(BASE_DIR, 'ml_model.joblib')
    SCALER_PATH = os.path.join(BASE_DIR, 'ml_scaler.joblib')
    
    # Over-cultivation threshold (if a crop occupies more than this % of a village's area, it's flagged)
    OVERCULTIVATION_THRESHOLD = 40.0
    
    # Supported crops
    CROPS = [
        'Wheat', 'Rice', 'Maize', 'Tomato', 'Onion',
        'Potato', 'Cotton', 'Soybean', 'Sugarcane', 'Barley'
    ]
    
    # Seasons
    SEASONS = ['Kharif', 'Rabi', 'Zaid', 'Annual']
    
    # Andhra Pradesh Locations
    AP_LOCATIONS = {
        'Chittoor': {
            'Tirupati (Urban)': ['Tirumala', 'Mangalam', 'Avilala', 'Perur'],
            'Chandragiri': ['Narasingapuram', 'Dornakambala', 'Thondawada'],
            'Srikalahasti': ['Urandur', 'Panagallu', 'Brahmanapalli']
        },
        'Guntur': {
            'Tenali': ['Kollipara', 'Nandivelugu', 'Kolakaluru'],
            'Bapatla': ['Ponnur', 'Karlapalem', 'Appikatla']
        },
        'Krishna': {
            'Vijayawada (Urban)': ['Machavaram', 'Gunadala', 'Bhavanipuram'],
            'Gudivada': ['Nandivada', 'Gudlavalleru']
        }
    }
    
    # Extract Districts for flat lists
    DISTRICTS = list(AP_LOCATIONS.keys())
    
    # Environmental factors
    SOIL_TYPES = ['Red', 'Black', 'Alluvial', 'Laterite', 'Sandy']
    WATER_AVAILABILITY = ['High', 'Medium', 'Low']
