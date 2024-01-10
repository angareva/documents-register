from src.documents_register import DocumentRegister

if __name__ == "__main__":
    
    documents_register = DocumentRegister()
    documents_register.upload_to_s3(base_path = documents_register.BASE_PATH_FILES, bucket_name = documents_register.S3_BUCKET_NAME)
    documents_register.extract_addresses(base_path = documents_register.BASE_PATH_FILES, output_folder = documents_register.OUTPUT_FOLER, 
                                         db_path = documents_register.DB_PATH, db_name = documents_register.DB_NAME)
    coordinates = documents_register.get_coordinates_from_database()
    documents_register.create_map(coordinates)
    