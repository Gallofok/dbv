from vapoursynth import core
import vapoursynth as vs
import sys
import math
import havsfunc as haf
import mvsfunc as mvf
import SHDdering as sd


core.max_cache_size=8000
core.num_threads=8


#Start################################
source = r"input 720p.mkv"

#input 8bit 720p video source and decode
source = core.lsmas.LWLibavSource(source,threads=0)

#select video length
#source = core.std.Trim(source, first=240, last=source.num_frames-1)

#set video framerate
source   = core.std.AssumeFPS(source, fpsnum=24000, fpsden=1001)

#Set up a control group
ref = core.resize.Bicubic(source, 1920, 1080, format=vs.YUV420P16, filter_param_a=0, filter_param_b=0.5)

### Modul 1 High quality image upscaling methode ###
### upscale with nnedi3 methode 720p to 1080p ###
# double the height of image and turn 180 degrees, then double the width of image and turn 180 degree, at last downscale to target resolution 1920x1080
source = core.znedi3.nnedi3(source,field=1,dh=True,nsize=4,nns=3,qual=2,pscrn=2).fmtc.resample(1280,1080,kernel='bicubic',a1=0,a2=0.5, sy=-0.5).std.Transpose()
source = core.znedi3.nnedi3(source,field=1,dh=True,nsize=4,nns=3,qual=2,pscrn=2).fmtc.resample(1080,1920,kernel='bicubic',a1=0,a2=0.5, sy=-0.5).std.Transpose()

# set video bitdepth to 16bit
src16  = mvf.Depth(source, 16) 
#set video bitdepth to 8bit
src8  = mvf.Depth(src16, 8)
### since here src16 and src8 are the original input video clip ###



# get video clip info
w = src16.width
h = src16.height
uw1 = w*2
uh1 = h*2
uw2 = round(w*1.6)
uh2 = round(h*1.6)
dw = round(w*0.8)
dh = round(h*0.8)



### Modul 2 denoise with BM3D ###
# nr means noise removal, 16 satnds for 16bits, y stands for Y-plane also called luma, uv stands for UV-plane also called chroma
# Apply BM3D denoise methode only to Y plane in colorspace OPP and then tansfer it back to Gray16
RGB_y = core.resize.Bicubic(src16, format=vs.RGBS, matrix_in_s="709", filter_param_a_uv=0, filter_param_b_uv=0.5, range_in_s="limited")
OPP_y = mvf.ToYUV(RGB_y, matrix='OPP')
flt_y = core.bm3d.Basic(OPP_y,  matrix=100, sigma=[1.6, 0, 0], profile="fast", group_size=8, bm_range=5)
flt_y = mvf.ToRGB(flt_y, matrix='OPP')
nr16y = core.resize.Bicubic(flt_y, format=vs.GRAY16, matrix_s="709", filter_param_a_uv=0, filter_param_b_uv=0.5, range_s="limited", dither_type='random')

# Apply BM3D denoise methoe to UV plane in colorspace OPP and then tansfer back to Gray16
# BM3D supoorts only YUV or Y input format, so we downscale the 1080p src16 with YUV420P format to a 540p clip with YUV444P format. 
# Apply BM3D denoise methode only to YUV plane in colorspace OPP and then tansfer it back to YUV444P16.
down   = core.fmtc.resample(src16, 960, 540, sx=-0.5, css='444', planes=[3, 2, 2])
RGB_uv = core.resize.Bicubic(down, format=vs.RGBS, matrix_in_s="709", filter_param_a_uv=0, filter_param_b_uv=0.5, range_in_s="limited")
OPP_uv = mvf.ToYUV(RGB_uv, matrix='OPP')
flt_uv = core.bm3d.Basic(OPP_uv, matrix=100, sigma=[0, 0.5, 0.5], profile="fast", group_size=8, bm_range=4)
flt_uv = mvf.ToRGB(flt_uv, matrix='OPP')
nr16uv = core.resize.Bicubic(flt_uv, format=vs.YUV444P16, matrix_s="709", filter_param_a_uv=0, filter_param_b_uv=0.5, range_s="limited", dither_type='random')

# take Y-plane from nr16y and UV-planes from nr16uv and combine them together
nr16 = core.std.ShufflePlanes([nr16y,nr16uv],[0,1,2],vs.YUV)

# accoding to MPEG-2 standard, set the alignment of clip to left.
nr16 = core.std.SetFrameProp(nr16, prop="_ChromaLocation", intval=0)

# Above we use the BM3D algorithm as a low-pass filter to separate high-frequency and low-frequency parts in the image
# the high-frequency parts is noise, also called grain, we store it with clip noise16
noise16 = core.std.MakeDiff(src16, nr16)
noise8  = mvf.Depth(noise16, 8)

# the low-frequency parts is nr16
# get Y-Plane of nr16 and nr8 for later processing
nr8    = mvf.Depth(nr16, depth=8)
nr8y  = core.std.ShufflePlanes(nr8, 0, vs.GRAY)
nr16y = core.std.ShufflePlanes(nr16, 0, vs.GRAY)



### Modul 3 various adaptive mask building ###
# rgvs is a high-pass filter library that integrates mean blur and median blur with multiple parameters. Mode=1~4 are median filters, and Mode17~20 are mean filters.
# RemoveGrain can also be used as a image blurring and smoothing filter
# We use it to smooth the pixel values of the luma plane to avoid negative effects caused by sharp changes in pixel values
# take the Y-plane of nr8 as luma infomatioin for mask generating
luma   = core.rgvs.RemoveGrain(nr8,[4,0]).rgvs.RemoveGrain([20,0])#.std.ShufflePlanes([0,0,0],vs.YUV).resize.Bilinear(format=vs.YUV420P8)

# Use the sobel operator in lib tcanny to caculate the gradient of each pixel value and store it as a continuous basic mask, which reflects the degree of pixel change between different regions in the image.
# The pixel value in the mask stands for the sharpness of pixel value changes of corresponding area in the video source, which means the corresponding position in video source is a line or not.
# mode=1 means using sobel operater, and sigma=0.5 means applying a gaussian blur with strength=0.5
# The basic mask is an 8bit YUV image with the range of pixel values interval [0,255].
mask = core.tcanny.TCanny(nr8, sigma=0.5, op=2, gmmax=255, mode=1, planes=[0,1,2])



### Modul 3.1 luma- and sharpness-adaptive sharpening mask for texture enhancement, also called eemask, mainly used to sharpen the line-area and texture-area ###
#generate a 16bit YUV mask with the range of pixel values interval [0,65535]
#get Y-plane of mask16
mask16 = core.tcanny.TCanny(nr16, sigma=0.5, mode=1, planes=[0,1,2])
#get U-plane of mask16
mask16_u = core.std.ShufflePlanes(mask16, [1,1,1], vs.YUV).resize.Spline36(w, h, format=vs.YUV420P16, src_left=0.25)
#get V-plane of mask16
mask16_v = core.std.ShufflePlanes(mask16, [2,2,2], vs.YUV).resize.Spline36(w, h, format=vs.YUV420P16, src_left=0.25)

# expr is a pixel value manipulator using postfix expressions, through which we can perform fine and complex mask adjustments to generate masks that can achieve various functions.
# x,y,z represent the three elements in the input clip array in order and the meaning of following postfix expressions is: [x/2 + y + z].
# We take both luma and chroma info into consideration and assign weights
mask16_yuv = core.std.Expr([mask16,mask16_u,mask16_v], ['x 2 / y + z +',''],vs.YUV420P16) 
mask8_yuv = core.resize.Bilinear(mask16_yuv, format=vs.YUV420P8)

# The Sobel operator is very sensitive to changes in brightness, but the luma pixel value is not linearly related to the brightness, but conforms to the gamma curve. This results in that lines in low-brightness ares are not easily detected by the sobel operator.
# Retinex can enhance the contrast of the picture by adjusting the gamma curve of the image, making lines more obvious. This way we can more easily separate the lines, especially in low brightness areas.
# get a big mask that frames or separate more lines
maskg16 = core.tcanny.TCanny(core.retinex.MSRCP(nr16y), sigma=0.8, mode=1, planes=0)

# merge the basic mask16 and big maskg16, so that lines in both bright areas and dark areas are not ignored.
# [max(x,y)]
linemask_y = core.std.Expr([mvf.GetPlane(mask16,0),maskg16], 'x y max',vs.GRAY16) 
linemask = core.std.ShufflePlanes([linemask_y,mask16], [0,1,2], vs.YUV)

# The continuous mask is binarized, and areas with pixel value exceeding the threshold 12800 is determined as lines.
linemask = core.std.Expr(linemask, ['x 12800 < 0 65535 ?',''],vs.YUV420P16).std.Maximum(0) # [x<12800?0:65535]
linemask = core.std.Minimum(linemask,0).rgvs.RemoveGrain([20,0])

# eemask is designed to sharpen the texture area strongly but only slightly sharpen the lines, so that the image looks sharper.
# Sharpness changes in low-luminance areas are more obvious for human eyes, so we take both line-strength and luma into consideration when sharpening the texture.
# We set up a continuous mask by establishing a quadratic function with an upper limit which takes line-strength and brightness as two variables, as a curve to adjust the sharpening-strength of different areas in the image.
eemask = core.std.Expr([mask8_yuv,luma],["x x * 16 * 255 y - dup * 0.16 * + 54000 min ",""],vs.YUV420P16) #[min(x*x*16+(235-y)^2*0.16, 54000)]

#The pixel value of the edge of the line changes significantly, while there is almost no pixel value change inside the line, so the line area in the mask may be hollow. To solve this problem, we can inflate the lines in the mask by one or three pixels with function Maximun, and then shrink them with Minimum to cover the hollow area.
eemask = core.std.Maximum(eemask,planes=[0,1,2]).std.Maximum(planes=[0,1,2]).std.Minimum(planes=[0,1,2]).rgvs.RemoveGrain(20)




### Modul 3.2 luma- and sharpness-adaptive debanding mask also called dbmask, which can fix corlor-banding without destroying textures  ###
# we must make sure that dbmask covers as many lines and textures as possible to prevent them from being smoothed by de-banding filters while debanding filters fix corlor banding. Meanwhile the edges of color banding should not be recognized as textures and covered by dbmask.
# Since tccany operator is sensitive to luma-change, we decide to set differnt threshold acording area brightness by gennerating 3 pre-dbmasks. That need a lot of parameter adjustments
# generate a small mask that covers relatively a few lines by binarizing the basic mask and make it a 16bit dbmask
dbmasks = core.std.Expr(mask,["x 7 < 0 65535 ?",""],vs.YUV420P16) #[x<7?0:65535]

#generate a big mask that covers relatively many lines by usding tccany operator, which is sensitive to luma-change in dark area
dbmaskb = core.tcanny.TCanny(nr8,sigma=1.3,t_h=6.0,op=2,planes=0)

#generate a giant mask that covers relatively more lines by usding tccany operator
dbmaskg = core.tcanny.TCanny(nr8,sigma=1.2,t_h=4.5,op=2,planes=0)

# use expr to merge 3 dbmasks according to luma and generating the final 16bit dbmask that covers almost all textures and lines but excludes corlor bandings
# We generate a binarized mask by using a three-segment piecewise function to create a curve that adjusts the strength of the deband according to the brightness and line strength.
dbmask  = core.std.Expr([dbmaskg,dbmaskb,dbmasks, nr8],["a 20 < 65535 a 48 < x 256 * a 96 < y 256 * z ? ? ?",""],vs.YUV420P16)  #[a<24? 65535 : a<36? x*256 : a<72? y*256 : z] and ormal parameters a stands for nr8 or luma 

# cover line hollows in dbmask
dbmask  = core.std.Maximum(dbmask,0).std.Maximum(0).std.Maximum(0).std.Minimum(0)

# smooth the dbmask with mean blur
dbmask  = core.rgvs.RemoveGrain(core.rgvs.RemoveGrain(dbmask,[20,0]),[20,0])




### Modul 3.3 luma- and sharpness-adaptive anti-alisasing mask, also called aamask, which can smooth lines, fix aliasing and link broken lines.  ###
# Aliasing is generally caused by upscaling of low-resolution images, and is usually only found in strong line-area. 
# So aamask need only cover strong lines but exclude textures.
# generate a 8bit basic aamask with sobel operator
aamask = core.tcanny.TCanny(nr8, sigma=0.5, op=2, gmmax=255, mode=1, planes=0).rgvs.RemoveGrain([4,0]).rgvs.RemoveGrain([4,0])

# Since the sobel operator has different sensitivities in different brightness area, we must set diffent threshold in aamask accordingly.
# We generate a binarized aamask by using a three-segment piecewise function to create a curve that adjusts the strength of the anti-aliasing according to the brightness and line strength.
aamask = core.std.Expr([aamask,luma],["y 48 < x 36 < 0 65535 ? y 72 < x 48 < 0 65535 ? x 64 < 0 65535 ? ? ? ",""],vs.YUV420P16) ##(y<56)?(x<28?0:65535):(x<80?0:65535)

# cover line hollows in dbmask
aamask = core.std.Maximum(aamask,0).std.Minimum(0)

# smooth the dbmask with mean blur
aamask = core.rgvs.RemoveGrain(aamask,[4,0]).rgvs.RemoveGrain([20,0])




### Modul 3.4 credit protecting mask, also called textmask, which can protect credits, staff list and subtitles from being damaged by other artifacts fixing filters   ###
# There are hard subtitles or staff list in many videos, which could be damaged by anti-alising filters and de-tinging filters. We must isolate the credits and leave them untouched.
# According to TV.709 standard, the pixel value range of the Y plane in a YUV420P8 clip is [16, 235], U and V range are [16,240].
# We take white subtitles for exsample. In this case, a white pixel has a ideal value of [235,128,128] in 8-bit YUV colorspace. But since video encoding is lossy, the true value is often accompanied by errors.

# separate YUV planes and meke them YUV444P16 clips
Y = core.std.ShufflePlanes(src16, 0, vs.YUV).resize.Bicubic(1920, 1080, format=vs.YUV420P16, filter_param_a=0, filter_param_b=0.5)
U = core.std.ShufflePlanes(src16, [1,1,1], vs.YUV).resize.Bicubic(1920, 1080, format=vs.YUV420P16, filter_param_a=0, filter_param_b=0.5)
V = core.std.ShufflePlanes(src16, [2,2,2], vs.YUV).resize.Bicubic(1920, 1080, format=vs.YUV420P16, filter_param_a=0, filter_param_b=0.5)

# Set the threshold for the pixels of the YUV plane respectively, and the error range is 3 under 8bit, that is, 768 under 16bit.

# Pixels that meet this condition are white areas, of which the large white blocks are often credit and we binarize them and get a textmaskb that covers a lot of white blocks. 
textmaskb = core.std.Expr([Y,U,V], ["x 52000 > y 32768 - abs 768 < and z 32768 - abs 768 < and 65535 0 ?","0"]) #[x>52000 && |y-32768|<768 && |z-32768|< 32768 ? 65535 : 0]

# But not all white blocks are credits, for exsample, stars in the night sky. We msut exclude them.
# Shrink the white blocks by 1 pixel with Minimum several times, and the tiny white blocks are eliminated. We get a textmasks that covers fewer white blocks.
textmasks = core.std.Minimum(textmaskb, 0).std.Minimum(planes=0).std.Minimum(planes=0).std.Maximum(0).std.Maximum(0).std.Maximum(0)

# After the intersection and union of the connected domains of the small mask, the left white blocks are all credits.
textmaskm = core.misc.Hysteresis(textmasks, textmaskb, planes=0)
textmask = core.std.Expr([textmaskb, textmaskm], "x y > x 0 ?")

# Inflate the edges of the textmask so that it can completely cover the credits.
textmask = core.std.Maximum(textmask,0).std.Maximum(0).std.Maximum(0)#.std.Maximum(0)#.std.Maximum(0)#.std.Maximum(0)#.std.Minimum(0)



### Modul 4 masked de-band with f3kdb ###
# Corlorbanding is very common in all kind of videos, especially in those with low bitrate or bad compression algorithm. Apart from the influence of poor compression algorithm and low bitrate, color banding will also appear in areas of large color blocks and low brightness areas. 
# In image processing and video encoding with a color depth of 8bit, color banding is difficult to avoid. So we perform all high-precision image processing at 16bit color depth, including debanding.
# There are several de-banding methodes, such as blurring, dither, and adding noise(SBMV algorithm of Sony). But none of them can fix the color banding perfectly, and can also bring the side effect of video volume expansion or loss of sharpness. 

# f3kdb is a good filter against corlor banding. It replaces the pixels that make up the color band with the median value of adjacent pixels, and dithers to fix corlor banding.

# 2pass f3kdb deband
debd  = core.f3kdb.Deband(nr16,range=8,y=56,cb=48,cr=48,grainy=0,grainc=0,output_depth=16)
debd  = core.f3kdb.Deband(debd,16,36,36,36,0,0,output_depth=16)

# apply some limit to the change of pixel values
debd  = mvf.LimitFilter(debd,nr16,thr=0.5,thrc=0.5,elast=2.0)

# apply dbmask to debanding. 
# All textures and lines are covered by dbmask so that they remain untouched, while bandings in plane areas are all fixed.
debd  = core.std.MaskedMerge(debd,nr16,dbmask,first_plane=True)




#### Modul 5 masked anti-aliasing algorithm with multiple kernels ###
# There are many anti-aliasing algorithms, some of which are widely used in 3D games, such as SSAA MSAA CSAA FSAA TAA. But they are generally not suitable for 2D animation.
# In these project we have proposes a new anti-aliasing method. Since characteristics of aliasing with interlaced images, we try to use de-interlace filters as kernels of anti-aliasing algorithm, which is SangNom, EEDI2, EEDI3, nnedi3.

# In most cases, aliasing mainly occurs in the Y plane, so this project takes the aliasing of the Y-plane as a sample.
# separate the Y-plane of video clip
oaa_y = core.std.ShufflePlanes(debd, 0, vs.GRAY)

# The above kernels are all top-aligned interlaced interpolation algorithms. They reduce the sharp changes in pixel values ​​through interpolation calculations, so as to achieve the effect of smoothing the lines.
# Since all of them are top-aligned, there will be always generating 0.5 pixel of center shift of the image. This is very different from normal center-aligned resize kernels like bicubic, spline or bilinear. We have to fix the shift with funtion fmtc.resample(sx=-0.5,sh=-0.5). It is really a keypoint of our anti-aliasing methodes. 

# Among all 4 types of anti-aliasing methodes, aatype 4 has the best effect.
aatype = 4
if aatype == 1:
	aa_y = core.fmtc.bitdepth(oaa_y,bits=8)	
	aa_y = core.sangnom.SangNom(aa_y, order=1, dh=True, aa=24).fmtc.resample(w,h,kernel='bicubic',a1=0,a2=0.5, sy=-0.5).fmtc.bitdepth(bits=8).std.Transpose()
	aa_y = core.sangnom.SangNom(aa_y, order=1, dh=True, aa=24).fmtc.resample(h,w,kernel='bicubic',a1=0,a2=0.5, sy=-0.5).std.Transpose()
	aa_y = core.rgvs.Repair(aa_y,oaa_y,mode=2)
elif aatype == 2:
	aa_y = core.eedi2.EEDI2(oaa_y,field=1,mthresh=10,lthresh=20,vthresh=20,maxd=24,nt=50).fmtc.resample(w,h,sy=-0.5, kernel='bicubic', a1=0, a2=0.5,).std.Transpose()
	aa_y = core.eedi2.EEDI2(aa_y,field=1,mthresh=10,lthresh=20,vthresh=20,maxd=24,nt=50).fmtc.resample(h,w,sy=-0.5, kernel='bicubic', a1=0, a2=0.5,).std.Transpose()
	# AWarpSharp2 is a filter that sharpens edges by warping them
	aa_y = core.warp.AWarpSharp2(aa_y, thresh=96, depth=1, planes=0)
elif aatype == 3:
	aa_y = core.znedi3.nnedi3(oaa_y,field=1,dh=True,nsize=4,nns=3,qual=2,pscrn=2).fmtc.resample(w,h,kernel='bicubic',a1=0,a2=0.5, sy=-0.5).std.Transpose()
	aa_y = core.znedi3.nnedi3(aa_y,field=1,dh=True,nsize=4,nns=3,qual=2,pscrn=2).fmtc.resample(h,w,kernel='bicubic',a1=0,a2=0.5, sy=-0.5).std.Transpose()
elif aatype == 4:
	#1 pass aa	
	aa_y = core.eedi2.EEDI2(oaa_y, field=1, mthresh=10, lthresh=20, vthresh=20, maxd=24, nt=50)
	aa_y = core.fmtc.resample(aa_y,w,uh2,sx=0,sy=-0.5,kernel='bicubic',a1=0,a2=0.5).std.Transpose()	
	aa_y = core.sangnom.SangNom(aa_y, order=1, dh=True, aa=36)
	aa_y = core.fmtc.resample(aa_y,h,w,sx=0,sy=-0.5,kernel='bicubic',a1=0,a2=0.5)

	#2 pass aa
	aa_y = core.eedi2.EEDI2(aa_y, field=1, mthresh=10, lthresh=20, vthresh=20, maxd=24, nt=50)
	aa_y = core.fmtc.resample(aa_y,h,uw2,sx=0,sy=-0.5,kernel='bicubic',a1=0,a2=0.5).std.Transpose()
	aa_y = core.sangnom.SangNom(aa_y, order=1, dh=True, aa=36)
	aa_y = core.fmtc.resample(aa_y,w,h,sx=0,sy=-0.5,kernel='bicubic',a1=0,a2=0.5)

	
# The anti-aliasing kernels have better effect than 3D games anti-aliasing algorithms, but result also win some negative side efftects, such as wrong connecting between lines and a little blurring of lines and textures.
aa_clip = core.std.ShufflePlanes([aa_y,debd], [0,1,2], vs.YUV)
# To prevent the negative side effects, we build aamask and allpy it. 
# aamask covers only stong lines, other areas remain untouched 
aaed    = core.std.MaskedMerge(debd, aa_clip, aamask, 0, True)



#### Modul 6 luma- and sharpness-adptive UnsharpMask, which can strongly sharpen the textures but slightly sharpen lines without obvious ringing or haloing artifacts ###
# Almost all processing above like de-banding, denoise, anti-aliasing have somehow blurring effect on video, which is agaisnt our purpose for high-quality restoration and upscaling of images. 
# To make image look sharp, clear and clean, we must apply some sharpening methode called luma- and sharpness-adptive UnsharpMask.
# The principle of usm is very simple. Separated The high-frequency part and the low-frequency part of the image with a low-pass filter, and then add the high-frequency part to the original image to make image look sharp.
# lowFreq = meanblur(src)
# highFreq = src - lowFreq
# sharp = src + highFreq 
dif    = core.std.MakeDiff(aaed, core.rgvs.RemoveGrain(aaed,[19,0]))
sharp  = core.std.MergeDiff(aaed, dif)

# UnsharpMask always result in heavy artifacts like ringing and haloing.
# To avoid extra ringing and haloing we have built the luma- and sharpness-adaptive eemask above and now apply it to aaed clip.
# According to the sharpening power curve we established, low-brightness areas and less-sharp areas such as textures are significantly sharpened,
# On the Contrary, high-brightness areas and strong lines are only slightly compensatory sharpened.
edge   = core.std.MaskedMerge(sharp, aaed, eemask, planes=0)


### Modul 7 Super HD de-ringing and dehaloing, called SHDering###
# Image compression and video encoding usually results in ringing and haloing, which are inevitably enhanced in shaepen-processing. Therefore we need some methode to fix ringing and halo artifacts.
# In these project we have proposes a de-ringing method, which is organized as a library SHDdering.py and because of its complexity and lack of time we decide not to go too further into its implementation principle in this project.
# ringing mostly occurs in Y-Plane, so we apply it only to Y-plane of video clip edge in this project.
# separate Y-Plane of edge
sharp_y = mvf.GetPlane(edge, 0)

# apply de-ringing methode
dr = sd.SHDdering_mod2(sharp_y, dering_pass=1, r=2.0)
# combine YUV planes
dred = core.std.ShufflePlanes([dr,edge], [0,1,2], vs.YUV)

# apply de-ringing only to lines, not to textures so that they won't get blurred.
dred = core.std.MaskedMerge(edge, dred, linemask, 0, True)

# exclude the credits from de-ringing object so that they won't get blurred. 
dred  = core.std.MaskedMerge(dred, debd, textmask, 0, False)




### Modul 8 masked luma-adptive denoise###
# Sincce we have separate the noises clip in Modul 1 and applied a lot of image restoration preocessding to the rest part, now we need to decide wether we should keep the radam noise.
# If we want a small size of the video file, it's better to forget the noise16 clip and set dred clip as output result.
# If we retain the random noise, it will require a higher bit rate, but it will make the picture look more natural.
# To solve the problem we have propose a best of both worlds approach, preserving the benefits of noise at the expense of a very small bit rate, called masked luma-adptive denoise.
# Human eye is more sensitive to noise in dark area than that in bright area. So we build a luma-adptive called nrweight to control how much noise should be retained in different brightness areas.
nullclip = core.std.Expr(src16,["32768"])
# Construct a continuous quadratic function curve, so that the value of mask increases rapidly with the increase of luma, which means, most noise in dark aress are rerained and most noise in bright area are removed. 
noisemask = core.std.Expr(luma, ["x 48 - dup * 3 * 3000 + "], vs.YUV420P16) #[max(x-32,0)]^2*5
noise16  = core.std.MaskedMerge(noise16,nullclip,noisemask,0,True)
# merge the video clip and noise16 clip
addnoise = core.std.MergeDiff(dred,noise16,0)


#set output clip
res = addnoise

ref = core.text.Text(ref, 'ref', 5)
res = core.text.Text(res, 'output', 5)

# to compare the reference or original video with the preocessed output clip, please set Debug=1
# the reference and output are interleave shown
# even frames are reference, odd frames are output 

Debug = 2
if  Debug == 1: # to compare the source and output
	compare = core.std.Interleave([ref,res])
	compare = mvf.ToRGB(compare,full=False,depth=8).set_output()
elif Debug == 2: #to check mask
	show = core.std.Interleave([nr16,eemask])
	show = mvf.Depth(show,depth=8).set_output()
elif Debug == 3: #to check each single plane
	show = debd
	nullclip = core.std.Expr(src16,["32768","32768","32768"])
	Y = core.std.ShufflePlanes(show,0,vs.GRAY)
	Y = core.std.ShufflePlanes([Y,nullclip],[0,1,2],vs.YUV)
	U = core.std.ShufflePlanes(show,1,vs.GRAY).fmtc.resample(1920, 1080,kernel='bicubic', a1=0, a2=0.5, sx=0.25)
	U = core.std.ShufflePlanes([U,nullclip],[0,1,2],vs.YUV)
	V = core.std.ShufflePlanes(show,2,vs.GRAY).fmtc.resample(1920, 1080,kernel='bicubic', a1=0, a2=0.5, sx=0.25)
	V = core.std.ShufflePlanes([V,nullclip],[0,1,2],vs.YUV)
	UV = core.std.ShufflePlanes([nullclip,show],[0,1,2],vs.YUV)
	compare = core.std.Interleave([Y,UV])
	compare = mvf.ToRGB(compare,full=False,depth=8).set_output()
else: #to encode the video with x265 or x264
	res = mvf.Depth(res,10).set_output()