from azure.storage.blob import BlobClient
import numpy as np
import pickle

class blob_uploader:
    def __init__(self):
        self.CONNECT_STR = "DefaultEndpointsProtocol=https;AccountName=farmgazerstorage;AccountKey=z2R8kCiNQL9Znn9CSJ6PRr9pLzoXssVQ6A/imdHr4k1djauW+2SIYTj9j79pg9bPi4EDhtYCByCA+ASttwYUBA==;EndpointSuffix=core.windows.net"
        self.container_name = "images"
    def upload(self,image, blob_name="my_blob.jpg",overwrite=True):
        # create connection
        blob = BlobClient.from_connection_string(conn_str=self.CONNECT_STR, container_name=self.container_name, blob_name=blob_name)
        
        # image can be either path or numpy
        if isinstance(image,str):
            try:
                with open(image, "rb") as data:  
                    blob.upload_blob(data,overwrite=overwrite)
            except Exception as e:
                print(e)
        
        elif isinstance(image, np.ndarray):
            data_in_bytes = pickle.dump(image)
            try:
                blob.upload_blob(data,overwrite=overwrite)
            except Exception as e:
                print(e)
        else:
            # default is bytes
            try:
                blob.upload_blob(image,overwrite=overwrite)
            except Exception as e:
                print(e)

#CONNECT_STR = 
# blob = BlobClient.from_connection_string(conn_str=CONNECT_STR, container_name="images", blob_name="my_blob.jpg")

if __name__ == "__main__":

    blob = blob_uploader()
    image_list = ["/home/pi/Pictures/NelsonFarm_Pea01_2024-02-09_1.jpg"]
    # image_list = ["/home/pi/Pictures/NelsonFarm_Pea02_2024-02-09_0.jpg",
    #               "/home/pi/Pictures/NelsonFarm_Pea03_2024-02-09_0.jpg",
    #               "/home/pi/Pictures/NelsonFarm_Pea04_2024-02-09_0.jpg",
    #               "/home/pi/Pictures/NelsonFarm_Wheat01_2024-02-09_0.jpg",
    #               "/home/pi/Pictures/NelsonFarm_Wheat02_2024-02-09_0.jpg",
    #               "/home/pi/Pictures/NelsonFarm_Wheat03_2024-02-09_0.jpg"]
    for image_pth in image_list:
        blob.upload(image_pth,blob_name = image_pth.split('/')[-1])