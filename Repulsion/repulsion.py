import numpy as N
import pylab as P
nr = 50
threshold = 5e-2
N.random.seed(10)

# Particles distributed over sphere
particles = N.random.random_sample((nr,3))
particles[:,0] = 1
particles[:,1] *= N.pi # 0 .. pi
particles[:,2] -= 0.5  # -pi .. pi
particles[:,2] *= 2*N.pi

# Particles distributed over sphere
next_pos = N.random.random_sample((nr,3))
next_pos[:,0] = 1
next_pos[:,1] *= N.pi # 0 .. pi
next_pos[:,2] -= 0.5  # -pi .. pi
next_pos[:,2] *= 2*N.pi

# Particles distributed over sphere
#particles = N.random.random_sample((nr,3))
#particles[:,0] = 1
#particles[:,1] = N.linspace(0,N.pi-0.01,nr)
#particles[:,2] = N.linspace(-N.pi,N.pi-0.01,nr)

# Particles distributed over sphere
#next_pos = N.random.random_sample((nr,3))
#next_pos[:,0] = 1
#next_pos[:,1] = N.linspace(0.01,N.pi,nr)
#next_pos[:,2] = N.linspace(-N.pi+0.01,N.pi,nr)
#next_pos[:,2] *= 2*N.pi


def polartocart(p_array):
    temp = p_array[:]+0  
    temp[:,0] = p_array[:,0]*N.sin(p_array[:,1])*N.cos(p_array[:,2])   
    temp[:,1] = p_array[:,0]*N.sin(p_array[:,1])*N.sin(p_array[:,2])
    temp[:,2]=p_array[:,0]*N.cos(p_array[:,1])
    return temp

xyz_particles = polartocart(particles)
next_pos = polartocart(next_pos)# N.zeros(xyz_particles.shape)
theta = N.zeros((nr,nr))
dP = N.zeros(xyz_particles.shape)

def cross_vv(d,e,res):
	res[0]=d[1]*e[2] - d[2]*e[1]
	res[1]=d[2]*e[0] - d[0]*e[2]
	res[2]=d[0]*e[1] - d[1]*e[0]
	
def cross_mm(a,b):
	#seperate the axes
	ax = a[:,0]
	ay = a[:,1]
	az = a[:,2]

	bx = b[:,0]
	by = b[:,1]
	bz = b[:,2]
	
	c = N.empty(a.shape)
	temp1 = N.empty(bx.shape)
	temp2 = N.empty(bx.shape)
	# cx
	N.multiply(ay,bz,temp1)
	N.multiply(az,by,temp2)
	N.subtract(temp1,temp2,c[:,0])
	# cy
	N.multiply(az,bx,temp1)
	N.multiply(ax,bz,temp2)
	N.subtract(temp1,temp2,c[:,1])
	# cz
	N.multiply(ax,by,temp1)
	N.multiply(ay,bx,temp2)
	N.subtract(temp1,temp2,c[:,2])
	return c

def cross_mv(a,b):
	#seperate the axes
	ax = a[:,0]
	ay = a[:,1]
	az = a[:,2]

	bx = b[0]
	by = b[1]
	bz = b[2]
	
	c = N.empty(a.shape)
	temp1 = N.empty(ax.shape)
	temp2 = N.empty(ax.shape)
	# cx
	N.multiply(ay,bz,temp1)
	N.multiply(az,by,temp2)
	N.subtract(temp1,temp2,c[:,0])
	# cy
	N.multiply(az,bx,temp1)
	N.multiply(ax,bz,temp2)
	N.subtract(temp1,temp2,c[:,1])
	# cz
	N.multiply(ax,by,temp1)
	N.multiply(ay,bx,temp2)
	N.subtract(temp1,temp2,c[:,2])
	return c



# V_i,j matrix
#Vij = pi x pj

for l,C in enumerate(N.logspace(-1,-6,5)): pass
for l,C in enumerate([1.0/(nr*10)]):
	print "C: %f"%C
	dPsum = 0
	f = open('dpsum_%i.dat'%l,'w')
	for k in xrange(2000):
		dPsum = 0
		print k
		V = N.empty(3)
		theta = N.arccos(N.dot(xyz_particles,xyz_particles.T))
		
		for i in xrange(nr):
			#theta = N.arccos(N.dot(xyz_particles,xyz_particles.T))
			Vij = cross_mv(xyz_particles,xyz_particles[i]) 
			dPi = cross_mv(Vij,xyz_particles[i])
			print theta[i,:].shape, N.resize(theta[i,:]**2,next_pos.shape[::-1]).T.shape,next_pos.shape,dPi.shape
			next_pos += C/N.resize(theta[i,:]**2/N.sum(dPi**2,axis=1)**0.5,next_pos.shape[::-1]).T*dPi
			next_pos /= N.resize(N.sum(next_pos**2,axis=1)**0.5,next_pos.shape[::-1]).T


 			for j in xrange(i+1,nr):
 				#theta = N.arccos(N.dot(xyz_particles[i],xyz_particles[j]))
 				#V = N.cross(xyz_particles[j],xyz_particles[i])
 				V = Vij[j]
 				cross_vv(xyz_particles[j],xyz_particles[i],V)
 
 				#dP[i]=N.cross(V,xyz_particles[i])
 				
				cross_vv(V,xyz_particles[i],dP[i])
				next_pos[i] += C/theta[i,j]**2*dPi[i]/N.dot(dPi[i],dPi[i])**0.5
				next_pos[i] /= N.dot(next_pos[i],next_pos[i])**0.5
 				
 				#dP[j] = cross(next_pos[j],V)
				cross_vv(next_pos[j],V,dP[j])
				next_pos[j] += C/theta[i,j]**2*dP[j]/N.dot(dP[j],dP[j])**0.5
				next_pos[j] /= N.dot(next_pos[j],next_pos[j])**0.5
 				dPsum += dP[i] + dP[j]
		
		
			#print i
 		xyz_particles = next_pos + 0
 		m = dPsum.sum()
 		f.write('%f\n'%m)
 		f.flush()
 		print xyz_particles
 		if k%500 == 0 or N.abs(m) <= threshold:
 			#fig = P.figure()
 			#P.plot(xyz_particles[:,0],xyz_particles[:,1])
 			#P.show()
 			#N.savetxt('test%i'%k,xyz_particles)
 			pass
 	#		print xyz_particles
 	#		for i in xrange(nr):
 	#			dist = xyz_particles[0] - xyz_particles[i]
 	#			print N.dot(dist,dist)**0.5
 		
 		if N.abs(m) < threshold:
 			print "Converged after %i to %f"%(k,m)
 			break
		#break
	f.close()
	#print dPsum
