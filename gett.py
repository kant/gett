import ett.preprocessing
import pdb
import ett.io_utils
import ett.reports
import argparse
import ett.network_building.models


parser = argparse.ArgumentParser()

parser.add_argument('traitfiles', nargs='+', type=argparse.FileType('r'))
parser.add_argument('--covariatefiles', nargs='+', type=argparse.FileType('r'))
parser.add_argument('--genotypematrix', nargs='+', type=argparse.FileType('r'))
parser.add_argument('--correctcovariates', nargs='+', type=str)
parser.add_argument('--selectbyvariance', type=float, default=1)
parser.add_argument('--transpose', action='store_true', default=False)
parser.add_argument('--clip', action='store_true', default=False)
parser.add_argument('--pcor', action='store_true', default=False)
parser.add_argument('--cor', action='store_true', default=False)
parser.add_argument('--naivecor', action='store_true', default=False)
parser.add_argument('--mindegree', type=int, default=0)
parser.add_argument('--corhthresh', type=float, default=0.)
parser.add_argument('--corsthresh', type=float, default=1.)
parser.add_argument('--zscores', action='store_true', default=False)
parser.add_argument('--savesteps', action='store_true', default=False)
parser.add_argument('--outdir', type=str, default='')

args = parser.parse_args()

report_matrices = args.clip

print 'Reading trait matrices'
Dtraits = [ett.io_utils.read_trait_matrix(f, transpose=args.transpose) for f in args.traitfiles]
trait_names = Dtraits[0].index
names = [args.outdir + f.name[f.name.rfind('/')+1:] for f in args.traitfiles]

if args.pcor:
    cor_analysis = True
    method_name = 'pcor'

if args.cor:
    cor_analysis = True
    method_name = 'cor'

if args.naivecor:
    cor_analysis = True
    method_name = 'naive'

if args.covariatefiles != None:
    print 'Reading covariate matrices'
    Dcovariates = [ett.io_utils.read_trait_matrix(f) for f in args.covariatefiles]
else:
    Dcovariates = None

if args.zscores:
    print 'Normalizing by z-scores'
    Dtraits = [ett.preprocessing.zscores(D) for D in Dtraits]

if args.correctcovariates != None:
    print 'Correcting for covariates'
    Dtraits = [ett.preprocessing.correct_covariates(Dtrait, Dcov, args.correctcovariates) for Dtrait, Dcov in zip(Dtraits, Dcovariates)]
    names = ett.io_utils.save_step(Dtraits, names, suffix='_cov_corrected', type='dataframe')

if args.selectbyvariance < 1:
    print 'Selecting by variance, top %s%%' % (args.selectbyvariance*100) 
    Dtraits = ett.preprocessing.select_traits_by_variance(Dtraits, frac=args.selectbyvariance)
    print 'Selected %s traits' % (len(Dtraits[0].index))
    names = ett.io_utils.save_step(Dtraits, names, suffix='_var_top_%s' % (args.selectbyvariance*100), type='dataframe')

if args.clip:
    print 'Performing CLIP analysis'
    clip_model = ett.network_building.models.CLIP(maxiter=10, mindegree=args.mindegree)
    Dtraits_reduced, prec_matrices, comm_vectors, llhood = clip_model(Dtraits)
    weight_matrices = prec_matrices

    ett.reports.community_report(names, comm_vectors, weight_matrices=weight_matrices, trait_names=trait_names)

if cor_analysis:
    print 'Performing %s analysis' % method_name
    shrink_model = ett.network_building.models.Shrinkage(method=method_name, thresh=args.corhthresh)
    matrices = shrink_model(Dtraits)
    ett.reports.network_report(names, matrices, trait_names=trait_names)
