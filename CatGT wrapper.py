import subprocess
import os
import glob
import time
import numpy as np

basefolder ='D:/SocialMemory_Neural/Ephys/M3/17122025'


def main(basefolder, tprimesavefolder, runcatGT=True, runsupercat=True, runtprime=False, prbnum='0', gbldmx=False, twoprobe=False, index=-1):
    supercatcmd = catgt(basefolder, runcatGT=runcatGT, prbnum=prbnum, gbldmx=gbldmx, twoprobe=twoprobe, index=index)
    supercat(basefolder, supercatcmd, runsupercat=runsupercat, prbnum=prbnum, twoprobe=twoprobe)
    tprime(basefolder, tprimesavefolder, runtprime=runtprime, runsupercat=runsupercat, prbnum=prbnum)

    return(supercatcmd)


def runprocess(command):
    start = time.time()
    print(f'Running: {command}\n')

    # Use Popen with stdout/stderr PIPE (captures CatGT progress)
    process = subprocess.Popen(
        command,
        shell=True,  # True on Windows to allow full path executables
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True  # returns strings instead of bytes
    )

    # Print output line by line as CatGT writes it
    for line in process.stdout:
        print(line, end='')  # already has newline

    process.wait() #wait for completion
    execution_time = time.time() - start
    print('completed: ' + str(np.around(execution_time, 2)) + ' s')


def catgt(basefolder, runcatGT=True, prbnum='0', gbldmx=False, twoprobe=False, index=-1, nisync=True, apextract=True):
    recordingfolders = glob.glob(basefolder + '/*_g*')
    catgtcmd = 'C:/Users/YKassem/Documents/CatGTWinApp/CatGT-win/CatGT.exe'
    supercatcmd = '-supercat='

    for f, ff in enumerate(recordingfolders):

        # check if f is in index e.g. index=[0,1,2,3]
        if isinstance(index, list) and f not in index and index != -1:
            continue

        rundir = os.path.split(ff)[1]
        rundir = rundir[:-3]
        gvalue = ff[-1]
        command = catgtcmd + ' -dir=' + basefolder + ' -run=' + rundir + ' -g=' + gvalue + ' -t=0'
        if apextract:
            command = command + ' -ap'
        if nisync:
            command = command + ' -ni'

        command = command + ' -prb_fld -t_miss_ok -prb=' + prbnum

        if twoprobe:
            command = command + ',1'

        command = command + ' -apfilter=butter,12,300,9000'
        if gbldmx:
            command = command + ' -gbldmx'
        else:
            command = command + ' -loccar_um=200,400'
        command = command + ' -gfix=0.4,0.1,0.02'

        if nisync:
            command = command + (' -xd=0,0,0,0,0 -xd=0,0,0,1,0 -xid=0,0,0,1,0 -xd=0,0,0,2,0 -xid=0,0,0,2,0'
                             ' -xd=0,0,0,3,0 -xid=0,0,0,3,0 -xd=0,0,0,4,0 -xid=0,0,0,4,0 -xd=0,0,0,5,0'
                             ' -xid=0,0,0,5,0 -xd=0,0,0,6,0 -xid=0,0,0,6,0 -xd=0,0,0,7,0 -xid=0,0,0,7,0')
        else:
            command = command + ' -xd=2,0,-1,6,0 -xid=2,0,-1,6,0'
        print(command)

        if runcatGT:
            runprocess(command)

        supercatpath = '{' + basefolder + ',' + os.path.split(ff)[1] + '}'
        supercatcmd = supercatcmd + supercatpath

    return supercatcmd

def supercat(basefolder, supercatcmd, runsupercat=True, prbnum='0', twoprobe=False):
    catgtcmd = 'C:/Users/YKassem/Documents/CatGTWinApp/CatGT-win/CatGT.exe'
    supercattemp = catgtcmd + ' -t=cat -prb_fld -ap -prb=' + prbnum
    if twoprobe:
        supercattemp = supercattemp + ',1'
    supercattemp = supercattemp + ' -xd=0,0,0,0,0 -xd=0,0,0,1,0 -xid=0,0,0,1,0 -xd=0,0,0,2,0 -xid=0,0,0,2,0 -xd=0,0,0,3,0 -xid=0,0,0,3,0'
    supercatcmd = supercattemp + ' -xd=0,0,0,4,0 -xid=0,0,0,4,0 -xd=0,0,0,5,0 -xid=0,0,0,5,0 -xd=0,0,0,6,0 -xid=0,0,0,6,0 -xd=0,0,0,7,0 -xid=0,0,0,7,0 -pass1_force_ni_ob_bin ' + supercatcmd + ' -dest=' + basefolder
    print(supercatcmd)

    if runsupercat:
        runprocess(supercatcmd)




def tprime(basefolder, savefolder, runtprime=True, runsupercat=True, prbnum='0'):
    tprimecmd = 'C:/TPrime/TPrime'
    recordingfolders = glob.glob(basefolder + '/*_g*')

    if runsupercat:
        recordingfolders = recordingfolders[:-1]
    if runtprime:
        for f, ff in enumerate(recordingfolders):
            foldername = os.path.split(ff)[1]
            foldername = foldername+'_imec'+prbnum
            spikeglxsync = glob.glob(ff+'/'+foldername+'/*500.txt')[0]
            nisync = glob.glob(ff+'/*500.txt')[0]
            #nicamsync = glob.glob(ff+'/*xid*txt')[0]
            nicamsync = glob.glob(ff + '/*0_6_0*txt')[0]
            savefile = savefolder+foldername[:-6]+'_spikeglx.txt'
            command = tprimecmd + ' -syncperiod=1.0 -tostream=' + spikeglxsync + ' -fromstream=1,' + nisync + ' -events=1,' + nicamsync + ',' + savefile
            print(command)


            runprocess(command)

if __name__ == "__main__":
    main(
        basefolder=basefolder,
        tprimesavefolder=None,  # or another path
        runcatGT=True,
        runsupercat=False,
        runtprime=False,
        prbnum='0'
    )

