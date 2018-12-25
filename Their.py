# def run_import_trials():
#     """
#     Given corresponding xslt file, the trials xml files are transformed and 
#     used to update the existing record or create new record in the Solr core 
#     (trials)
#     """

#     batch = 500
#     url = "http://localhost:8983/solr/trials/update?commit=true"

#     # - read xsl file
#     if not os.path.isfile(cfg.PATHS['xsl-trial']):
#         logger.log('ERROR', 'xsl-trial [{}] cannot be found'.
#                    format(cfg.PATHS['xsl-trial']), die=True, printout=True)
#     else:
#         logger.log('DEBUG', 'reading xsl file for clinical trials xml files')

#     try:
#         xslt = et.parse(cfg.PATHS['xsl-trial'])
#         transformer = et.XSLT(xslt)
#     except:
#         e = sys.exc_info()[0]
#         logger.log('ERROR', 'xsl parsing error: {}'.format(e), printout=True)

#     # read all trial source files (*.xml) in trial data sub-directories
#     # (total num of files must be 241006)
#     trial_files = []
#     for root, dirs, files in os.walk(cfg.PATHS['data-trials']):
#         if not re.match(r"\d+", root.split(os.sep)[-1]):
#             continue
#         for file in files:
#             if not file.endswith('xml'):
#                 continue
#             trial_files.append(os.path.join(root, file))
#     logger.log('INFO', '{} trials found from {}'. \
#                format(len(trial_files), cfg.PATHS['data-trials']))

#     # if skip_files is given, read the list
#     skip_files = []
#     if cfg.skip_files and os.path.isfile(cfg.skip_files):
#         with open(cfg.skip_files) as f:
#             skip_files = f.read().splitlines()
#         skip_fh = open(cfg.skip_files, 'a', buffering=1)

#     docs_collated = 0
#     skipped_files = 0
#     completed_files = 0
#     for i, file in enumerate(trial_files):
#         attempts = 3
#         if file in skip_files:
#             skipped_files += 1
#             if skipped_files % 1000 == 0:
#                 logger.log('INFO', 'skipping files [{}/{}]'. \
#                            format(skipped_files, len(skip_files)))
#             continue
#         logger.log('INFO', 'parsing a trial file {}'.format(file))

#         if docs_collated == 0:
#             req = et.Element('add')

#         # - transform trial xml to solr update format
#         trial_trans = transformer(et.parse(file))
#         # - pre-indexing nlp process
#         utils.age_normalize(trial_trans)
#         if docs_collated < batch:
#             req.append(trial_trans.getroot())
#             docs_collated += 1

#         # - run update, if docs_collated reached batch or end of files
#         if docs_collated == batch or i == len(trial_files)-1:
#             docs_collated = 0
#             headers = {'content-type': 'text/xml; charset=utf-8'}

#             while attempts > 0:
#                 try:
#                     r = requests.post(url, data=et.tostring(req),
#                                      headers=headers)
#                 except requests.exceptions.RequestException as e:
#                     logger.log('ERROR', 'request exception: {}'.format(e))
#                     logger.log('ERROR', r, die=True, printout=True)

#                 if r.status_code != 200:
#                     attempts -= 1
#                     logger.log('ERROR', r.text)
#                     logger.log('ERROR', 'data: \n' + str(et.tostring(req)))
#                     r.raise_for_status()
#                     if attempts < 0:
#                         logger.log('CRITICAL', 'terminating', die=True,
#                                    printout=True)
#                 else:
#                     completed_files += 1
#                     # - log the results
#                     logger.log('INFO',
#                                'importing trial files in progress {}/{}'. \
#                                format(i+1, len(trial_files)), printout=True)
#                     if cfg.skip_files:
#                         skip_fh.write(file + '\n')

#                     if cfg.sms and completed_files % 5000 == 0:
#                         logger.sms('importing trial files {}/{}'. \
#                                    format(i+1, len(trial_files)))
#                     break
#     logger.log('INFO', 'importing trials completed', printout=True)
