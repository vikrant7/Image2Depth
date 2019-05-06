import numpy as np
import cv2
import json
from model import *
import cv2
from matplotlib import pyplot as plt
from scipy.misc import toimage
import matplotlib.pyplot as plt


class Trainer(object):
	"""docstring for Trainer."""
	def __init__(self, TrainDictName="train.json",ValDictName="val.json",TrainFromScratch=True):
		with open(TrainDictName) as f:
			self.TrainDict = json.load(f)
		with open(ValDictName) as f:
			self.ValDict = json.load(f)

		self.BatchSize=25
		self.TotalEpochs=20
		self.TrainList=self.TrainDict.keys()
		self.ValList=self.ValDict.keys()

		self.InputPlaceholder=tf.placeholder(tf.float32,shape=(None,None,None,3))
		self.O1,self.O2,self.O3,self.O4=Build(self.InputPlaceholder)

		self.L4=tf.losses.absolute_difference(self.O4,self.DP4)
		self.L3=tf.losses.absolute_difference(self.O3,self.DP3)
		self.L2=tf.losses.absolute_difference(self.O2,self.DP2)
		self.L1=tf.losses.absolute_difference(self.O1,self.DP1)

		self.DP4=tf.placeholder(tf.float32,shape=(None,None,None,1))
		self.DP3=tf.placeholder(tf.float32,shape=(None,None,None,1))
		self.DP2=tf.placeholder(tf.float32,shape=(None,None,None,1))
		self.DP1=tf.placeholder(tf.float32,shape=(None,None,None,1))

		self.LossTensor=self.L1+self.L2+self.L3+self.L4
		self.optimizer=tf.train.AdamOptimizer(learning_rate=0.0001).minimize(LossTensor)

		self.TrainL1Loss,self.TrainL2Loss,self.TrainL3Loss,self.TrainL4Loss=[],[],[],[]
		self.ValL1Loss,self.ValL2Loss,self.ValL3Loss,self.ValL4Loss=[],[],[],[]

		self.Session = tf.Session()
		self.Session.run(tf.initialize_all_variables())
		self.Saver = tf.train.Saver()
		if not TrainFromScratch:
			self.Checkpoint=input("please name the checkpoint with directory =>")
			self.Saver.restore(self.Session, self.Checkpoint)

	def FetchTrainBatch(self):
		for i in range(len(self.TrainList)//self.BatchSize):
			image,depth=[],[]
			for j in range(self.BatchSize):
				img=cv2.imread(self.TrainList[i*self.BatchSize+j])
				img=cv2.resize(im,(800,640))[-288:,:,:]
				img=img.astype(float)/255.0

				gt=cv2.imread(self.TrainDict[self.TrainList[i*self.BatchSize+j]],0)
				gt=cv2.resize(gt,(800,640))[-288:,:])
				gt=gt.astype(float)/255.0
				gt=np.expand_dims(gt,axis=-1)

				image.append(im)
				depth.append(gt)
			yield np.array(image),np.array(depth)

	def FetchValBatch(self):
		for i in range(len(self.ValList)//self.BatchSize):
			image,depth=[],[]
			for j in range(self.BatchSize):
				img=cv2.imread(self.ValList[i*self.BatchSize+j])
				img=cv2.resize(im,(800,640))[-288:,:,:]
				img=img.astype(float)/255.0

				gt=cv2.imread(self.ValDict[self.ValList[i*self.BatchSize+j]],0)
				gt=cv2.resize(gt,(800,640))[-288:,:])
				gt=gt.astype(float)/255.0
				gt=np.expand_dims(gt,axis=-1)

				image.append(im)
				depth.append(gt)
			yield np.array(image),np.array(depth)

	def MetricsAndHousekeeping(self,Epoch=0):
		save_path = self.Saver.save(self.Session,"./tmp/"+str(Epoch)+"model.ckpt")
		print("model saved at"+save_path)
		plt.plot(self.TrainL1Loss,'r')
		plt.plot(self.TrainL2Loss,'g')
		plt.plot(self.TrainL3Loss,'b')
		plt.plot(self.TrainL4Loss,'y')
		plt.savefig("Trainlosses.png")
		plt.close()
		print("Plot saved")


	def train(self):
		for epoch in range(self.TotalEpochs):
			self.MetricsAndHousekeeping(Epoch=epoch)
			DataObject=self.FetchTrainBatch()
			step=0
			for dat,GT in DataObject:
				dat,GT4=FetchTrainBatch(i)

				GT3=GT4[:,::2,::2,:]
				GT2=GT4[:,::4,::4,:]
				GT1=GT4[:,::8,::8,:]

				Loss,_,l1,l2,l3,l4,O=sess.run([LossTensor,optimizer,L1,L2,L3,L4,O4],feed_dict={DP1:GT1,DP2:GT2,DP3:GT3,DP4:GT4,InputPlaceholder:dat})
				cv2.imshow("Output",O[0,:,:,0])
				cv2.imshow("image",dat[0,:,:,:])
				cv2.waitKey(1)

				step+=1
				print("L 1",l1,"L 2",l2,"L 3",l3,"L 4",l4,"L1 Log",Loss,"epoch",epoch,"step",step)
				self.TrainL1Loss.append(l1)
				self.TrainL2Loss.append(l2)
				self.TrainL3Loss.append(l3)
				self.TrainL4Loss.append(l4)
			self.Validate()

	def Validate(self):
		DataObject=self.FetchTrainBatch()
		for dat,GT in DataObject:
			dat,GT4=FetchValBatch()

			GT3=GT4[:,::2,::2,:]
			GT2=GT4[:,::4,::4,:]
			GT1=GT4[:,::8,::8,:]

			Loss,l1,l2,l3,l4,O=sess.run([LossTensor,L1,L2,L3,L4,O4],feed_dict={DP1:GT1,DP2:GT2,DP3:GT3,DP4:GT4,InputPlaceholder:dat})

			step+=1
			print("L 1",l1,"L 2",l2,"L 3",l3,"L 4",l4,"L1 Log",Loss,"epoch",epoch,"step",step)
			self.ValL1Loss.append(l1)
			self.ValL2Loss.append(l2)
			self.ValL3Loss.append(l3)
			self.ValL4Loss.append(l4)
		plt.plot(self.ValL1Loss,'r')
		plt.plot(self.ValL2Loss,'g')
		plt.plot(self.ValL3Loss,'b')
		plt.plot(self.ValL4Loss,'y')
		plt.savefig("Vallosses.png")
		plt.close()
		print("Validation done")
