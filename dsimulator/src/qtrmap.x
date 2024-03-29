# STATUS: maps OK -- now need extension to individual CCDs and a wrapper script.

# QTRMAP: "Quick Trace Mapping" -- generate the data and/or mappings needed
# for the "quick-trace".  In this case, all pre- and post-grating elements
# are used to produce a single map each; only the grating x-form and grating
# equation are needed with these maps to produce all info.
#
# based largely on TRACE; is TRACE is changed we need to review here.
# Also, this is a good opportunity to start to "clean up" these codes.  Eg,
# build "spec_optics.x", break "pt_xfm" into the three parts required here, etc.



include	<math.h>
include	"keck.h"
include	"deimos.h"
include	"instrument.h"

# THESE FROM QEXTR -- FIX PROLIFERATION OF CONSTANTS!!
define	D_1	20018.4D0	# see deimos.h PPLDIST
define	R_CURV	2124.71D0	# ditto; r=83.65in in this case = R_IMSURF


procedure	t_qtrmap()

char	amap[SZ_FNAME], bmap[SZ_FNAME]		# input file name (x,y,w)
double	t1, p1
double	t2, p2
double	t3, p3, o3
double	roll3
pointer	fda, fdb

double	e1[3,3], a2[3,3], a3[3,3], a4[3,3]	# transforms
real	ccd[NCCD,3]				# CCD geometry
double	sys[NPARAM]				# system parameters

int	i	# TMP?

int	clgeti()
real	clgetr()
pointer	open()

begin
	t1 = clgetr ("trace.coll_angle")
	p1 = clgetr ("trace.coll_phi")
	t2 = clgetr ("trace.t2")
	p2 = clgetr ("trace.p2")
	t3 = clgetr ("trace.mu")
	p3 = clgetr ("trace.p3")		# z-misalignment of tilt angle
	o3 = clgetr ("trace.o3")		# independent yaw
	roll3 = clgetr ("trace.roll3")	# roll, assuming p3=0

	CAM_FOC(sys) = clgetr ("trace.cam_foc")
	ORDER(sys) = clgeti ("trace.norder")
	GRLINES(sys) = 1.e-3 * clgeti ("trace.gmm")
	X_OPT(sys) = clgetr ("trace.x_optaxis")
	Y_OPT(sys) = clgetr ("trace.y_optaxis")
	MOS_ROT(sys) = DEGTORAD(clgetr ("trace.mos_rotation"))
# TMP HARDCODES:

COL_DST(sys) = 2197.1
COL_ERR(sys) = DEGTORAD(t1)
COL_PHI(sys) = DEGTORAD(p1)

TNT_ANG(sys) = DEGTORAD(71.5 + t2)
TNT_PHI(sys) = DEGTORAD(90. + p2)

MU(sys) = DEGTORAD (t3)
GR_YERR(sys) = DEGTORAD (roll3)
GR_ZERR(sys) = DEGTORAD (o3)
CAM_ANG(sys) = DEGTORAD (clgetr ("trace.cam_angle"))
CAM_PHI(sys) = DEGTORAD (clgetr ("trace.cam_phi"))

	XFO_TLT(sys) = 0.
	YFO_TLT(sys) = -1.81E-4
call eprintf ("Special Y_TILT ADDED! %9.4g\n")
call pargd (YFO_TLT(sys))

do i = 1, 8 {
	CN_XERR(sys,i) = 0.
	CN_YERR(sys,i) = 0.
	CN_RERR(sys,i) = 0.
}


	call clgstr ("amap", amap, SZ_FNAME)
	fda = open (amap, NEW_FILE, TEXT_FILE)

	call clgstr ("bmap", bmap, SZ_FNAME)
	fdb = open (bmap, NEW_FILE, TEXT_FILE)



	call fprintf (fda, "# COL_ERR=%7f  COL_PHI=%7f  TNT_ANG=%7f  TNT_PHI=%7f\n")
		call pargd (RADTODEG(COL_ERR(sys)))
		call pargd (RADTODEG(COL_PHI(sys)))
		call pargd (RADTODEG(TNT_ANG(sys)))
		call pargd (RADTODEG(TNT_PHI(sys)))

	call fprintf (fdb, "# CAM_ANG=%7f  CAM_PHI=%7f  CAM_FOC=%7f  MOS_ROT=%7f  X_OPT=%5f  Y_OPT=%5f\n")
		call pargd (RADTODEG(CAM_ANG(sys)))
		call pargd (RADTODEG(CAM_PHI(sys)))
		call pargd (CAM_FOC(sys))
		call pargd (RADTODEG(MOS_ROT(sys)))
		call pargd (X_OPT(sys))
		call pargd (Y_OPT(sys))



	call qtrmap (fda, fdb, e1, a2, a3, a4, ccd, sys)

	call close (fda)
	call close (fdb)

end


procedure	qtrmap (fda, fdb, e1, a2, a3, a4, ccd, sys)

pointer	fda, fdb				# output file pointers
double	e1[3,3], a2[3,3], a3[3,3], a4[3,3]	# transforms
real	ccd[NCCD,3]				# CCD geometry
double	sys[NPARAM]				# system parameters

int	i, j
int	nx, ny			# number of steps in x,y
int	nex			# number of extra steps beyond real bdry

double	xstep, ystep
double	x, y
double	tanx, tany
double	r[3]

bool	reverse					# provide the reverse maps?

bool	clgetb()
int	clgeti()

begin
# Set up the tranforms
	call setup (e1, a2, a3, a4, ccd, sys)

# Get the params
	nx = clgeti ("nx")
	ny = clgeti ("ny")
	nex = clgeti ("nextra")
	reverse = clgetb ("reverse")

	xstep = 364. / (nx-1)
	ystep = 220. / (ny-1)
	xstep = 500. / (nx-1)
	ystep = 300. / (ny-1)
call eprintf ("\n###############\nNB!!! SKY PROJECTION!\n\n")

# Write the amap
	call eprintf ("writing alpha map (NB hardcodes) %d %d %d\n")
		call pargi (nx); call pargi (ny); call pargi (nex)
	do j = -nex, ny+nex {
#		y = j * ystep
		y = j * ystep + 180.
		do i = -nx-nex, nx+nex {
			x = i * xstep
#			call pre_grating (x, y, e1, a2, sys, r)
			call sky_grating (x, y, e1, a2, sys, r)
			tanx = (-r[1] / -r[3])
			tany = (-r[2] / -r[3])

			if (reverse) {
			    call fprintf (fda, "%10.7f %10.7f %10.5f %10.5f\n")
				call pargd (tanx)
				call pargd (tany)
				call pargd (x)
				call pargd (y)
			} else {
			    call fprintf (fda, "%10.5f %10.5f %10.7f %10.7f\n")
				call pargd (x)
				call pargd (y)
				call pargd (tanx)
				call pargd (tany)
			}
		}
	}

	ny = nx
	xstep = 4596. / (nx-1)
	ystep = 4596. / (ny-1)

# Write the amap
	call eprintf ("writing beta map (NB hardcodes) %d %d %d\n")
		call pargi (nx); call pargi (ny); call pargi (nex)

	do j = -ny-nex, ny+nex {
		y = j * ystep
		do i = -nx-nex, nx+nex {
			x = i * xstep
			if (x*x+y*y > (5080.**2))
				next
			call ics_post_grating (x, y, a4, sys, r)
			tanx = (-r[1] / -r[3])
			tany = (-r[2] / -r[3])
			if (reverse) {
			    call fprintf (fdb, "%10.4f %10.4f %11.8f %11.8f\n")
				call pargd (x)
				call pargd (y)
				call pargd (tanx)
				call pargd (tany)
			} else {
			    call fprintf (fdb, "%11.8f %11.8f %10.4f %10.4f\n")
				call pargd (tanx)
				call pargd (tany)
				call pargd (x)
				call pargd (y)
			}
		}
	}


			
end



procedure	ics_post_grating (x, y, a, sys, r)

double	x, y
double	a[3,3]				# camera tranformation
double	sys[NPARAM]			# system parameters

double	theta, phi
double	xp, yp, rp 
double	xpp, ypp
double	cosp, sinp, cost, sint

double	r[3]			# coord vector

begin

# 8. Remove the mosaic transform
	cosp = cos (-MOS_ROT(sys))
	sinp = sin (-MOS_ROT(sys))
	xpp = x - X_OPT(sys)
	ypp = y - Y_OPT(sys)
	xp =  cosp * xpp + sinp * ypp
	yp = -sinp * xpp + cosp * ypp

# 7. The display coords are different than the x,y,z convention adopted so far:

	xp = -xp
	yp = -yp

# 6. Convert to x,y in focal plane:
	rp = sqrt (xp*xp + yp*yp)
	theta = atan (rp * PIX_SZ / CAM_FOC(sys))
	phi = atan2 (yp, xp)

# 5. Camera distort theta (phi unchanged)
	call cam_distort (theta, theta, NO)

# 4. Convert into x,y,z:

	cosp = cos (phi)
	sinp = sin (phi)
	cost = cos (theta)
	sint = sin (theta)

	r[1] = cosp * sint
	r[2] = sinp * sint
	r[3] = cost

# 3. transform out of camera system
	call gen_xfm (r, a, NO)

	
end


#
# SKY_GRATING: calculate the direction vector _before_ the grating, as seen
# from the sky.  This is a modified version of pre_grating, found in qextr.
#

procedure	sky_grating (xarcs, yarcs, e1, a2, sys, r)

double	xarcs, yarcs
double	e1[3,3], a2[3,3]			# pre-grating transforms
double	sys[NPARAM]				# system parameters
double	r[3]

double	a1[3,3]

double	xfp, yfp			# x,y points in FP (tan projection)
double	x, y, pa
double	phi, theta
double	phin, thetan
double	cost, sint, cosp, sinp

double	rp, hm


begin
	xfp = FL_TEL * tan (DEGTORAD(xarcs/3600.))
	yfp = FL_TEL * tan (DEGTORAD(yarcs/3600.)) / cos (DEGTORAD(xarcs/3600.))
	call gnom_to_dproj (xfp, yfp, x, y)		# (allowed)

#	pa = 0.
#	x = xmm
#	y = ymm
#	call mask_to_proj (x, y, pa, x, y, pa)

# convert to r[3]:
	rp = sqrt (x*x + y*y)
	hm = R_CURV - sqrt (R_CURV*R_CURV - rp*rp)
	theta = atan (rp / (D_1-hm))
	phi = atan2 (y, x)

	cosp = cos (phi)
	sinp = sin (phi)
	cost = cos (theta)
	sint = sin (theta)

	r[1] = cosp * sint
	r[2] = sinp * sint
	r[3] = cost

# COLLIMATOR:
	call coll_angle (x, y, sys, theta, phi)

	thetan = theta
	phin = phi + HALFPI
	cosp = cos (phin)
	sinp = sin (phin)
	cost = cos (thetan)
	sint = sin (thetan)

	a1[1,1] = cosp
	a1[1,2] = sinp
	a1[1,3] = 0.
	a1[2,1] = -cost*sinp
	a1[2,2] = cost*cosp
	a1[2,3] = sint
	a1[3,1] = sint*sinp
	a1[3,2] = -sint*cosp
	a1[3,3] = cost

	call refl (r, a1)
	call gen_xfm (r, e1, YES)
	call refl (r, a2)
end

