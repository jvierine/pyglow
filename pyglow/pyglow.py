
# TODO
# [ ] see what's in the neutral output

def say_hello():
    print "hi from pyglow.py!"

class Point:
    def __init__(self, dn, lat, lon, alt):
        import numpy as np

        nan = float('nan')
        
        # record input:
        self.dn = dn
        self.lat = lat
        self.lon = lon
        self.alt = alt

        self.doy = self.dn.timetuple().tm_yday
        self.utc_sec = self.dn.hour*3600. + self.dn.minute*60.
        self.utc_hour = self.dn.hour
        self.slt_hour = np.mod(self.utc_sec/3600. + self.lon/15., 24)
        self.iyd = np.mod(self.dn.year,100)*1000 + self.doy

        # initialize variables:
        # ---------------------

        # for kp, ap function
        self.kp       = nan
        self.ap       = nan
        self.f107     = nan
        self.f107a    = nan
        self.kp_daily = nan
        self.ap_daily = nan

        # for iri:
        self.n = nan
        ions = ['O+', 'H+', 'HE+', 'O2+', 'NO+']
        self.ni={}
        for ion in ions:
            self.ni[ion] = nan
        
        self.Ti = nan
        self.Te = nan
        self.Tn_iri = nan

        # for msis:
        self.Tn_msis = nan
        self.nn = nan

        # for hwm 93/07:
        self.u = nan
        self.v = nan
        self.hwm_version = nan

        # for igrf:
        self.Bx  = nan
        self.By  = nan
        self.Bz  = nan
        self.B   = nan
        self.dip = nan

        # call the models:
        self.get_indices()

    def __repr__(self):
        out = ""
        out += "%20s" % "dn = "\
                + self.dn.__str__() + '\n'
        out += "%20s" % "(lat, lon, alt) = "\
                + "(%4.2f, %4.2f, %4.2f)\n" % (self.lat, self.lon, self.alt)

        # Indices:
        out += "\nGeophysical Indices:\n---------------------\n"
        out += "%20s" % "kp = "\
                + "%4.2f\n" % self.kp
        out += "%20s" % "ap = "\
                + "%4.2f\n" % self.ap
        out += "%20s" % "f107a = "\
                + "%4.2f\n" % self.f107a

        # IGRF:
        out += "\nFrom IGRF:\n-----------\n"
        out += "%20s" % "(Bx, By, Bz) = "\
                + "(%4.3e, %4.3e, %4.3e)\n" % (self.Bx, self.By, self.Bz)
        out += "%20s" % "B = "\
                + "%4.3e\n" % (self.B)
        out += "%20s" % "dip = "\
                + "%4.2f\n" % (self.dip)

        # HWM:
        out += "\nFrom HWM:\n------------\n"
        out += "%20s" % "hwm version = "\
                + "%s\n" % (self.hwm_version)
        out += "%20s" % "(u, v) = "\
                + "(%4.2f, %4.2f)\n" % (self.u, self.v)

        #out += "%20s" % "n      = %4.2e\n" % self.n

        return out

    def get_indices(self):
        import sys
        sys.path.append("../indices/")
        from get_kpap import get_kpap
        self.kp, self.ap, self.f107, self.f107a, \
                self.kp_daily, self.ap_daily  = get_kpap(self.dn)

    def run_iri(self):
        from iri12py import iri_sub as iri
        #sys.path.append("./modules")
        import os, sys
        import numpy as np
        import pyglow

        jf = np.ones((50,))
        jf[4]  = 0 # 5  foF2 - URSI (what does that mean?)
        jf[5]  = 0 # 6  Ni - RBV-10 & TTS-03 
        jf[20] = 0 # 21 ion drift not computed
        jf[21] = 0 # 22 ion densities in m^-3
        jf[22] = 0 # 23 Te_topside (TBT-2011)
        jf[28] = 0 # 29 (29,30) => NeQuick
        jf[29] = 0 # 30  
        jf[33] = 0 # 34 messages [on|off]
        
        my_pwd = os.getcwd()

        iri_data_path = '/'.join(pyglow.__file__.split("/")[:-1]) + "/iri_data/"
        #print "changing directory to \n", iri_data_path

        os.chdir(iri_data_path)
        [outf,oarr] = iri(jf,0,\
                self.lat,\
                self.lon,\
                int(self.dn.year),\
                -self.doy,\
                (self.utc_sec/3600.+25.),\
                self.alt,\
                self.alt+1,\
                1)
        os.chdir("%s" % my_pwd)

        self.Te        = outf[3,0] # electron temperature from IRI (K)
        self.Ti        = outf[2,0] # ion temperature from IRI (K)
        self.Tn_iri    = outf[1,0] # neutral temperature from IRI (K)
        self.n         = outf[0,0] # electron density (m^-3)
        self.ni['O+']  = outf[4,0] # O+ Density (%, or m^-3 with JF(22) = 0)
        self.ni['H+']  = outf[5,0] # H+ Density (%, or m^-3 with JF(22) = 0)
        self.ni['HE+'] = outf[6,0] # HE+ Density (%, or m^-3 with JF(22) = 0)
        self.ni['O2+'] = outf[7,0] # O2+ Density (%, or m^-3 with JF(22) = 0)
        self.ni['NO+'] = outf[8,0] # NO+ Density (%, or m^-3 with JF(22) = 0)
        
        return
    
    def run_msis(self):
        from msis00py import gtd7 as msis
        from get_apmsis import get_apmsis
        import numpy as np 

        apmsis = get_apmsis(self.dn)
        [d,t] = msis(self.doy,\
                self.utc_sec,\
                self.alt,\
                self.lat,\
                np.mod(self.lon,360),\
                self.slt_hour,\
                self.f107a,\
                self.f107,\
                apmsis,\
                48)
        self.Tn_msis = t[1] # neutral temperature from MSIS (K)
        self.nn = d

    def run_hwm93(self):
        from hwm93py import gws5 as hwm93
        import numpy as np

        w = hwm93(self.iyd,\
                self.utc_sec,\
                self.alt,\
                self.lat,\
                np.mod(self.lon,360),\
                self.slt_hour,\
                self.f107a,\
                self.f107,\
                self.ap)
        self.v = w[0]
        self.u = w[1]
        self.hwm_version = '93'

    def run_hwm07(self):
        from hwm07py import hwmqt as hwm07
        import pyglow
        import os
        import numpy as np

        my_pwd = os.getcwd()

        hwm07_data_path = '/'.join(pyglow.__file__.split("/")[:-1]) + "/hwm07_data/"
        #print "changing directory to \n", hwm07_data_path

        os.chdir(hwm07_data_path)
        aphwm07 = [float('NaN'), self.ap]
        w = hwm07(self.iyd,\
                self.utc_sec,\
                self.alt,\
                self.lat,\
                np.mod(self.lon,360),\
                self.slt_hour,\
                self.f107a,\
                self.f107,\
                aphwm07)
        os.chdir("%s" % my_pwd)
        self.v = w[0]
        self.u = w[1]
        self.hwm_version = '07'

    def run_igrf(self):
        from igrf11py import igrf11syn as igrf
        import numpy as np

        x, y, z, f = igrf(0,\
                self.dn.year,\
                1,\
                self.alt,\
                90.-self.lat,\
                np.mod(self.lon,360),\
                )

        h = np.sqrt(x**2 + y**2)
        dip = 180./np.pi * np.arctan2(z,h)
        self.Bx  = x/1e9
        self.By  = y/1e9
        self.Bz  = z/1e9
        self.B   = f/1e9
        self.dip = dip
 
class Line(Point):

    def __init__(self, dn, lat, lon, alt):
        Point.__init__(self, dn, lat, lon, alt)

        self.points = []
        self.igrf_tracefield()

        self.lat = []
        self.lon = []
        self.alt = []
        self.n = []
        self.dn = dn
        for p in self.points:
            p.run_iri()
            self.lat.append( p.lat )
            self.lon.append( p.lon )
            self.alt.append( p.alt )
            self.n.append( p.n )

    def igrf_tracefield(self, target_ht=90., step=15.):
        import numpy as np

        # Go North:
        lla_north = self._igrf_tracefield_hemis(target_ht, step)

        # Go South:
        lla_south = self._igrf_tracefield_hemis(target_ht, -step)

        # Stack them together:
        lla = np.vstack( [ np.flipud(lla_north)[:-1,:], lla_south ])
        
        # for lat,lon,alt in lla.....
        for kk in range(lla.shape[0]):
            self.points.append(\
                    Point(self.dn,lla[kk,0],lla[kk,1],lla[kk,2]/1e3))
        return


    def _igrf_tracefield_hemis(self, target_ht, step):
        import numpy as np
        import coord
        from numpy import array as arr
        
        lat = float(self.lat)
        lon = float(self.lon)
        alt = float(self.alt)
        target_ht = float(target_ht)
        step = float(step)
    
        target_ht = target_ht*1e3
        step = step*1e3
    
        lla = np.array([lat, lon, alt*1e3])
    
        lla_field = lla
      
        """ Step 1: trace the field along a given direction """
        TOLERANCE = 10 # [m]
        i = 0
        while (lla[2] > target_ht):
            # convert to ECEF:
            ecef = coord.lla2ecef(lla)
    
            # Grab field line information:    
            p = Point(self.dn, lla[0], lla[1], lla[2]/1e3)
            p.run_igrf()

            N = p.Bx # North
            E = p.By # East
            D = p.Bz # Down
            A = p.B  # Total

            # Step along the field line
            ecef_new =  ecef + coord.ven2ecef(lla,[(-D/A*step), (E/A*step), (N/A*step)] )  
            
            # Convert to lla coordinates:
            lla = coord.ecef2lla(ecef_new)
    
            # add the field line to our collection:
            lla_field = np.vstack( [lla_field, lla] )       
            i = i + 1
    
        """ Step 2: Make the last point close to target_ht """
        while (abs(lla[2]-target_ht) > TOLERANCE):
            my_error = lla[2]-target_ht
            old_step = step
            # find out how much we need to step by:
            step = -np.sign(step)*abs(lla[2]-target_ht)
    
            ecef = coord.lla2ecef(lla)

            p = Point(self.dn, lla[0], lla[1], lla[2]/1e3)
            p.run_igrf()

            N = p.Bx # North
            E = p.By # East
            D = p.Bz # Down
            A = p.B  # Total

            # trace the field, but use the modified step:
            ecef_new = ecef + coord.ven2ecef(lla,np.array([(-D/A), (E/A), N/A])*step/(-D/A) )  
            # TODO : I changed this, is this correct?
    
            lla = coord.ecef2lla(ecef_new)
    
        # replace last entry with the point close to target_ht:
        lla_field[-1,:] = lla
    
        return lla_field

if __name__=="__main__":
    from datetime import datetime, timedelta
    import numpy as np

    dn = datetime(2002, 3, 25, 12, 0, 0)
    lat = 42.5
    lon = 0.
    alt = 250.
    o = Point(dn, lat, lon, alt)


    o.run_iri()
    o.run_msis()
    o.run_hwm93()
    o.run_hwm07() 
    o.run_igrf()



    #l = Line(dn, lat, lon, alt)


    '''
    dn_start = datetime(2000,1,1)
    dn_end   = datetime(2005,1,1)
    dns = [dn_start + timedelta(days=kk) for kk in range((dn_end-dn_start).days)]
    f107a = []
    for dn in dns:
        p = Point(dn, 0, 0, 300)
        f107a.append( p.f107a )

    from matplotlib.pyplot import *
    figure(1); clf()
    plot(dns, f107a)
    grid()
    draw(); show();
    kmin = np.argmin(f107a)
    kmax = np.argmax(f107a)
    print dns[kmin], f107a[kmin]
    print dns[kmax], f107a[kmax]
    '''




