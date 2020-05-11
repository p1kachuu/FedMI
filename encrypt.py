import numpy as np
import time
import random
import sys
from Paillier import Paillier
import numpy as np
from tensorflow.keras.models import load_model
from PaillierT import *
pk = 106504846927713258539210316352790353882162270818938504115679857002260675662663868186195764884050680158387910786319360594118394158988265190760518018383856211127828957901489657873023505978079816086418739645927283447419458899692329924108808874227987115411899682260014549514951147887170486841798910991527563787031
# sk = 53252423463856629269605158176395176941081135409469252057839928501130337831331934093097882442025340079193955393159680297059197079494132595380259009191928095065151915289367689982455840657486912258413401572506241074544947119824452974828937040817794939696289107948598574946928408925445955735399657880921851834532
sk0 = 54855930201116632641914550201734837220485525426007065029466442940440673772419705970813895348208263159742688478459129247731713857177365553634825552276367324516346187031786306150802038434735290492339330384379801798027124569500779162307451089750093030627109298663414427445131497800085849749634024347358542372461
sk1 = 528263650766877275932919921275458380550543961093497477356667001002190960569906705037348241426890603320296905249902545411899980565104699481525395013083289919906788843166852065603134770235415707290164749583789441810850832781623851990840776543655776327558528828244093855325709600191354192736049492520613431498957714208045764913122574737569943826011788959926798124402788379653090725454990045036592914769126494422572187731075509498879745801584379601010007621367864804590645273888204960338257862937602162099525408980497074640289031307143033792937497075244923230682737479352568014183130936599767095734221130371448350230272638502691551373629094406275678800840784362667694784261488146233066695574075744648433431482140238179116738788574012227237304795591045355859733794618060425836222302945518099009055852859238631425371684572622665096919144896582077874967525312270451177973383001999795518490801787848072180747116708992370883255538447
# pk, sk = generate_paillier_key(1024)
# psys = Paillier()
# n = -100000
# m = 1223456
# p0, p1 = psys.key_splitting()
# pk = psys.n
# cm = psys.enctypt(m)
# cn = psys.enctypt(n)
# c = (cn * cm)
# c0 = psys.share_dec(c, p0)
# c1 = psys.share_dec(c, p1)
# print("------------------------------------------")
# print("[pk]", psys.n)
# print("------------------------------------------")
# print("[sk]", psys.lambdaa)
# print("------------------------------------------")
# print("[p0]", p0)
# print("------------------------------------------")
# print("[p1]", p1)
# print("------------------------------------------")
# print("[c0]", c0)
# print("------------------------------------------")
# print("[c1]", c1)
# print("------------------------------------------")
# print("[cm]", psys.dec_with_shares(c0, c1))
# print("------------------------------------------")
# print("[m]", psys.decrypt(c))

model = load_model('./model/covid19_VGG16.h5')
weights = model.get_weights()
en_params = []
print(weights[27])
start = time.clock()
for i in range(27, 28):
    weights[i] = weights[i] * 1000000
    weights[i] = weights[i].astype(np.int)
    shape = weights[i].shape
    temp_arr = np.array([encrypt(int(x), pk) for x in np.nditer(weights[i])])
    en_params.append(temp_arr.reshape(shape))
end = time.clock()
#print(en_params[0])
print("密钥分割加密时间{}s".format(end - start))
c0_params = []
c1_params = []
cm_params = []
for i in range(len(en_params)):
    shape = en_params[i].shape
    temp_arr = np.array([share_dec(int(x), pk, sk0) for x in np.nditer(en_params[i], flags=['refs_ok'])])
    c0_params.append(temp_arr.reshape(shape))
for i in range(len(en_params)):
    shape = en_params[i].shape
    temp_arr = np.array([share_dec(int(x), pk, sk1) for x in np.nditer(en_params[i], flags=['refs_ok'])])
    c1_params.append(temp_arr.reshape(shape))
print(len(c0_params)==len(c1_params))
for i in range(len(en_params)):
    shape = en_params[i].shape
    temp_arr = np.array([dec_with_shares(int(s0), int(s1), pk) for (s0, s1) in zip(np.nditer(c0_params[i], flags=['refs_ok']), np.nditer(c1_params[i], flags=['refs_ok']))])
    temp_arr = temp_arr / 1000000
    cm_params.append(temp_arr.reshape(shape))
print(cm_params[0])





# public_key, secret_key = paillier.generate_paillier_keypair()
# weights = model.get_weights()
# en_params = []
# start = time.clock()
# for i in range(26, len(weights)):
#     shape = weights[i].shape
#     temp_arr = np.array([public_key.encrypt(float(x)) for x in np.nditer(weights[i])])
#     en_params.append(temp_arr.reshape(shape))
# end = time.clock()
# print("python-paillier加密时间{}s".format(end - start))