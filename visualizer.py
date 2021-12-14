#!/usr/bin/python3
import math
import pickle 
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from deg2km import ll2xy
import os
import cv2
import natsort

class Visualizer(object):

    def __init__(self, pickle_path, output_path):
        self.file_path = pickle_path
        self.output_path = output_path
        self.timestamp = []
        self.latitude = []
        self.longitude = []
        self.x = []
        self.y = []
        self.z = []
        self.l = []
        self.w = []
        self.h = []
        self.tff = []

    def homogeneous_transformation(self,alpha,xyz,lon,lat):
        t = [lon,lat,0]
        translational_vector=np.array(t)
        translational_vector=np.expand_dims(translational_vector,axis=1)
        rot_mat = np.array([[1,0,0], 
                        [0,math.cos(alpha),-math.sin(alpha)],
                        [0,math.sin(alpha),math.cos(alpha)]])
        extra_row_gen = np.array([[0,0,0,1]])
        hm_mat = np.append(rot_mat,translational_vector,axis=1)
        hm_mat = np.append(hm_mat,extra_row_gen,axis=0)
        xyz=np.append(xyz,np.array([1]),axis=0)
        #from IPython import embed;embed()
        tff = np.matmul(hm_mat, xyz)
        tff = tff[:-1]
        return tff

    def cuboid_data2(self,o, size=(1,1,1)):
                X = [[[0, 1, 0], [0, 0, 0], [1, 0, 0], [1, 1, 0]],
                    [[0, 0, 0], [0, 0, 1], [1, 0, 1], [1, 0, 0]],
                    [[1, 0, 1], [1, 0, 0], [1, 1, 0], [1, 1, 1]],
                    [[0, 0, 1], [0, 0, 0], [0, 1, 0], [0, 1, 1]],
                    [[0, 1, 0], [0, 1, 1], [1, 1, 1], [1, 1, 0]],
                    [[0, 1, 1], [0, 0, 1], [1, 0, 1], [1, 1, 1]]]
                X = np.array(X).astype(float)
                for i in range(3):
                    X[:,:,i] *= size[i]
                X += np.array(o)
                return X
    
    def plotCubeAt2(self,positions,sizes=None,colors=None, **kwargs):
                if not isinstance(colors,(list,np.ndarray)): colors=["C0"]*len(positions)
                if not isinstance(sizes,(list,np.ndarray)): sizes=[(1,1,1)]*len(positions)
                g = []
                for p,s,c in zip(positions,sizes,colors):
                    g.append(self.cuboid_data2(p, size=s))
                return Poly3DCollection(np.concatenate(g),  
                                        facecolors=np.repeat(colors,6), **kwargs)


    def visualize(self):
        with open(self.file_path, 'rb') as f:
            pickle_file = pickle.load(f)

        ego_logs = pickle_file.get('ego_logs')
        detected_object_logs = pickle_file.get('detected_object_logs')

        for i in range(len(ego_logs)):
            self.timestamp.append(ego_logs[i]['timestamp'])
            self.latitude.append(ego_logs[i]['latitude'])
            self.longitude.append(ego_logs[i]['longitude'])
        for j in range(len(detected_object_logs)):
            self.x.append(detected_object_logs[j]['x'])
            self.y.append(detected_object_logs[j]['y'])
            self.z.append(detected_object_logs[j]['z'])
            self.l.append(detected_object_logs[j]['l'])
            self.w.append(detected_object_logs[j]['w'])
            self.h.append(detected_object_logs[j]['h'])

        self.x = np.asarray(self.x)
        self.y = np.asarray(self.y)
        self.z = np.asarray(self.z)

        if len(self.x.shape) !=2 and len(self.y.shape) !=2 and len(self.z.shape) !=2:
            self.x=np.expand_dims(self.x, 1)
            self.y=np.expand_dims(self.y, 1)
            self.z=np.expand_dims(self.z, 1)

        self.pcl_xyz=np.hstack([self.x,self.y,self.z])
        #deg2m conversion invoked from MATLAB code
        x_lon = []
        y_lat =[]
        for i,j in zip(self.latitude,self.longitude):
            x,y = ll2xy(i,j, slat=70, slon=0, hemi='s', units='m')
            x_lon.append(x)
            y_lat.append(y)

        #init heading angle 
        heading_angle = []   
        #considering lat lon as x and y
        for i in range(len(self.timestamp)-1):
            x1= x_lon[i]
            x2 = x_lon[i+1]
            y1 = y_lat[i]
            y2 = y_lat[i+1]
            angle = math.atan2(y2 - y1,x2 - x1)
            angle *=  180 / math.pi
            heading_angle.append(angle)

        heading_angle.insert(0,0)

        #transformation matrix from local- LiDAR to world coordinates
        #transformation around x direction-yaw angle from local to world coordinates
    
        for i in range(len(self.timestamp)-1):
            self.tff.append(self.homogeneous_transformation(heading_angle[i],self.pcl_xyz[i,:],x_lon[i],y_lat[i]))

        tff_x=[]
        tff_y = []
        tff_z=[]
        for i in range(len(self.tff)):
            tff_x.append(self.tff[i][0])
            tff_y.append(self.tff[i][1])
            tff_z.append(self.tff[i][2])

        for i in range(len(detected_object_logs)-1):

            positions = [(self.tff[i][0],self.tff[i][1],self.tff[0][2])]
            sizes = [(self.l[i],self.w[i],self.h[i])]
            colors = ["red"]
            
            positions1 = [(x_lon[i],y_lat[i],heading_angle[i])]
            colors1 = ["blue"]
            fig = plt.figure()
            ax = fig.gca(projection='3d')
            #ax.set_aspect('equal')
            pc = self.plotCubeAt2(positions,sizes,colors=colors, edgecolor="k")
            #pc1 = matplotlib.axes.Axes.arrow(x_lon[i], y_lat[i], 
            #        0, 0, 0.001, head_width=1, 
            #       head_length=1, fc='r', ec='r')
            #pc1 = plt.plot(x_lon[i], y_lat[i], marker = ">")
            #pc1 = self.plotCubeAt2(positions1,sizes=[(10,10,10)],colors=colors1, edgecolor="k")
            ax.add_collection3d(pc)
            #ax.add_collection3d(pc1)
            ax.plot(x_lon[i], y_lat[i], marker = (3,0,heading_angle[i]),markersize=20)

            ax.set_xlim([min(x_lon)-40,max(x_lon)+40])
            ax.set_ylim([min(y_lat)-40,max(y_lat)+40])
            ax.set_zlim([-12e-02,10])
            fig1 = plt.gcf()
            #plt.show()
            plt.draw()
            fig1.savefig(self.output_path+str(i)+'.png', dpi=100)

        image_folder = self.output_path
        length_file = len(self.output_path.split('/'))
        length_file = self.output_path.split('/')[length_file-1]
        length_file = length_file.split('.')[0]
        video_name = self.output_path+'/'+length_file+'.avi'
        images = [img for img in sorted(os.listdir(image_folder)) if img.endswith(".png")]
        images = natsort.natsorted(images,reverse=False)
        frame = cv2.imread(os.path.join(image_folder, images[0]))
        height, width, layers = frame.shape

        video = cv2.VideoWriter(video_name, 0, 1, (width,height))

        for image in images:
            video.write(cv2.imread(os.path.join(image_folder, image)))

        cv2.destroyAllWindows()
        video.release()

        #clear images
        files_in_directory = os.listdir(self.output_path)
        filtered_files = [file for file in files_in_directory if file.endswith(".png")
        for f in filtered_files:
	        path_to_file = os.path.join(directory, f)
            os.remove(path_to_file)





