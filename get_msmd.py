
import glob
import math
import sys
import pickle

def get_info(filename, provenance):
    info = {}
    msmd.open(filename)
    info['band'] = int(msmd.namesforspws(0)[0].split("#")[1].split("_")[2])
    position = msmd.phasecenter()
    temp = msmd.fieldnames()
    if len(temp) > 1:
        # HK 13-08-2019
        # Given that, it may be most practical to simply check that all of
        # the 'fieldnames' entries are the same, and if they are, continue
        # as usual with the metadata harvesting.  If it were straightforward
        # to do, it might also be worth generating some kind of flag / note
        # / separate file about the fact that the field is given 3 times
        # rather than 1, in case this is something that we need to bring up
        # with the ALMA archive team at a later date.
        fields = list(set(temp))
        logging.warning('Repeated field names for MS {}'.format(filename))
        if len(fields) > 1:
            raise ValueError("Expected ms with just one target")
    else:
        fields = temp
    if msmd.nobservations() > 1:
        raise ValueError("Exepected ms with just one observation")
    info['field'] = fields[0]
    spws = msmd.spwsforfield(fields[0])
    spectral_windows = []
    for idx in spws:
        spectral_windows.append((min(msmd.chanfreqs(idx)), max(msmd.chanfreqs(idx))))
    info['spectral_windows'] = spectral_windows
    dates = msmd.timerangeforobs(0)
    info['start_date'] = dates['begin']['m0']['value']
    info['end_date'] = dates['end']['m0']['value']
    info['project'] = msmd.projects()[0]
    scans = msmd.scansforfield(info['field'])
    itime = 0
    itime_len = 0
    for scan in scans:
        itime += len(msmd.timesforscan(scan)) * msmd.exposuretime(scan)['value']
        itime_len += len(msmd.timesforscan(scan))
    info['itime'] = itime
    info['resolution'] = itime_len
    info['effexposuretime'] = msmd.effexposuretime()['value']

    # HK 19-08-19
    # energy: sample size - if this is the number of spectral resolution
    # elements, we could add this!  Adding up all of the elements in the
    # output for msmd.chanwidths() (run over each of the 4 spectral
    # windows) would give the answer here.

    # HK 19-08-19
    # energy: resolution - I don't see this listed in the caom2 model parameters
    # (http://www.opencadc.org/caom2/#Energy), but would this represent the
    # frequency resolution?  If so, it could be added in, with the
    # complication that this will be variable for the different spectral
    # windows, and hence one merged range of frequencies might have multiple
    # frequency resolutions.  The msmd.chanwidths function (run per spectral
    # window) will give this information in frequency space - this is still
    # TODO until there's a resolution on the whether or not to split on
    # Energy Band, because that will provide an answer as to 'which value to
    # use'
    sample_size = 0
    energy_resolution = 0
    for ii in spws:
        kwargs = {'spw': ii}
        temp = msmd.chanwidths(**kwargs)
        sample_size += len(temp)
    info['sample_size'] = sample_size
    info['energy_resolution'] = energy_resolution
    info['provenance'] = provenance
   

if __name__ == '__main__':
   project = sys.argv[-1]
   pk_file = "/home/jkavelaars/{}_md.pk".format(project)
   md = {}
   if os.access(pk_file, os.F_OK):
     with open(pk_file, 'r') as pk:
        md = pickle.load(pk)
        print md
   for filename in glob.glob('uid__*.ms.split.cal'):
       try:
          md[filename] = get_info(filename)
       except Exception as ex:
          sys.stderr.write(str(filename)+":  "+str(ex)+"\n")
   with open(pk_file, 'w') as pkl:
       pickle.dump(md, pkl)
   for key in md.keys():
      print key, md[key]['project']

