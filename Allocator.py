import socket, struct

# Convert IP address from dotted decimal form (string) to a 32bit integer value
def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]

# Convert IP address from integer form to dotted decimat form
def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))

class allocator:
    indices = {}			# offsets allocated to subnet size in respective buckets
    buckets = []			# list of buckets allocated
    def __init__(self):
        self.indices = {k: [] for k in range(32)}
        self.buckets.append(0)
        self.addRestrictedRanges()

    def addRestrictedRanges(self):
        # Add the restricted range 192.0.0.0/8
        self.buckets.append(192)
        self.indices[8].append([192])

        # Add the restricted range 169.154.0.0/16
        self.buckets.append(169)
        self.indices[16].append([169, 154])

    def getNext (self, subnet):
        bucket, offset = self.addNext (subnet)
        startIP = (bucket*(1<<24)) + (offset*(1<<(32-subnet)))
        endIP = startIP + (1<<(32-subnet)) - 1
        net = (int2ip(startIP)+'/'+str(subnet))
        # print self.buckets, bucket, offset
        return [int2ip(startIP), int2ip(endIP), subnet, net]

    def getFirstNotIn (self, list, r):
        for i in range(1,r): 
            if i>=len(list) or list[i] != i-1:
                list.insert(i,i-1)
                return i-1
        return -1

    def addNext (self, subnet):
        # iterate over list of subnets
        for i in range(0,len(self.indices[subnet])):
            # check if bucket is not full
            if (len(self.indices[subnet][i]) < (1<<(subnet-8))):
                # print "subnet",subnet,"index",i, self.indices[subnet][i]
                return [self.indices[subnet][i][0], self.getFirstNotIn(self.indices[subnet][i], (1<<(subnet-8)))]
        bucket = self.getFirstNotIn (self.buckets, 255)
        self.indices[subnet].append([bucket, 0])
        return [bucket, 0]

    def checkIfAllocated (self, ip):
        ip = ip2int (ip)
        for i in range(32):
    	    for bckt in self.indices[i]
                    for j in range (1, len (bckt)):
                        start = (bckt[i][0]*(1<<24)) + (bckt[i][j]*(1<<(32-i)))
            		    end = start + (1<<(32-i)) - 1
            		    if ip >= start or ip <= end
            		        return True
        return False



class test_allocator:
    def __init__():
        print "Testing Allocator"

    def testAll(self):
        A = allocator()
        print "Next range for subnet /8:", A.getNext(8)
        print "Next range for subnet /16:", A.getNext(16)
        print "Next range for subnet /24:", A.getNext(24)
        print "Next range for subnet /16:", A.getNext(16)
        print "Next range for subnet /24:", A.getNext(24)
        print "Next range for subnet /24:", A.getNext(24)
        print "Next range for subnet /16:", A.getNext(16)
        print "Next range for subnet /23:", A.getNext(23)
        print "Next range for subnet /23:", A.getNext(23)
