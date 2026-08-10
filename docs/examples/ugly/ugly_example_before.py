"""Parameters module."""
import argparse
import textwrap

# import torch
# import torch.nn.parallel
# import torch.backends.cudnn as cudnn
# import torch.utils.data


class Parameters:
    """Base options."""

    def __init__(self):
        """Constructor."""
        self.parser = argparse.ArgumentParser()
        self.initialized = False

    def initialize(self):
        """Initialize."""
        # Define training set depending on the user name
        default_root = "default"
        default_out = "out"
        # Dataset parameters
        self.parser.add_argument(
            "--dataset",
            type=str,
            default="objects_folder_multi",
            help="dataset name: [shapenet, objects_folder, objects_folder]",
        )  # laptop,pistol
        # self.parser.add_argument('--dataset', type=str, default='objects_folder', help='dataset name: [shapenet, objects_folder]')
        self.parser.add_argument(
            "--root_dir", type=str, default=default_root, help="dataset root directory"
        )
        self.parser.add_argument(
            "--root_dir1", type=str, default=default_root, help="dataset root directory"
        )
        self.parser.add_argument(
            "--root_dir2", type=str, default=default_root, help="dataset root directory"
        )
        self.parser.add_argument(
            "--root_dir3", type=str, default=default_root, help="dataset root directory"
        )
        self.parser.add_argument(
            "--root_dir4", type=str, default=default_root, help="dataset root directory"
        )
        self.parser.add_argument(
            "--synsets",
            type=str,
            default="",
            help="Synsets from the shapenet dataset to use",
        )
        self.parser.add_argument(
            "--classes",
            type=str,
            default="bowl",
            help="Classes from the shapenet dataset to use",
        )  # ,cap,can,laptop
        self.parser.add_argument(
            "--workers", type=int, default=0, help="number of data loading workers"
        )
        self.parser.add_argument(
            "--light_change",
            type=int,
            default=2000,
            help="number of data loading workers",
        )
        self.parser.add_argument(
            "--toy_example", action="store_true", default=False, help="Use toy example"
        )
        self.parser.add_argument(
            "--use_old_sign", action="store_true", default=True, help="Use toy example"
        )
        self.parser.add_argument(
            "--use_quartic", action="store_true", default=False, help="Use toy example"
        )
        self.parser.add_argument(
            "--rescaled", action="store_true", default=False, help="Use toy example"
        )
        self.parser.add_argument(
            "--full_sphere_sampling",
            action="store_true",
            default=False,
            help="Use toy example",
        )
        self.parser.add_argument(
            "--full_sphere_sampling_light",
            action="store_true",
            default=True,
            help="Use toy example",
        )
        self.parser.add_argument(
            "--random_rotation",
            action="store_true",
            default=True,
            help="Use toy example",
        )
        self.parser.add_argument(
            "--stoch_enc", action="store_true", default=False, help="Use toy example"
        )
        self.parser.add_argument(
            "--only_background",
            action="store_true",
            default=False,
            help="Use toy example",
        )
        self.parser.add_argument(
            "--only_foreground",
            action="store_true",
            default=False,
            help="Use toy example",
        )
        self.parser.add_argument(
            "--rotate_foreground",
            action="store_true",
            default=False,
            help="Use toy example",
        )
        self.parser.add_argument(
            "--use_penality", action="store_true", default=True, help="Use toy example"
        )
        self.parser.add_argument(
            "--use_mesh",
            action="store_true",
            default=True,
            help="Render dataset with meshes",
        )
        self.parser.add_argument(
            "--gen_model_path", type=str, default=None, help="dataset root directory"
        )
        self.parser.add_argument(
            "--gen_model_path2", type=str, default=None, help="dataset root directory"
        )
        self.parser.add_argument(
            "--dis_model_path", type=str, default=None, help="dataset root directory"
        )
        self.parser.add_argument(
            "--dis_model_path2", type=str, default=None, help="dataset root directory"
        )
        self.parser.add_argument(
            "--bg_model",
            type=str,
            default="../../../data/halfbox.obj",
            help="Background model path",
        )
        self.parser.add_argument(
            "--gz_gi_loss",
            type=float,
            default=0.0,
            help="grad z and grad img consistency.",
        )
        self.parser.add_argument("--pixel_samples", type=int, default=1, help="Samples per pixel.")

        # Network parameters
        self.parser.add_argument(
            "--gen_type",
            type=str,
            default="dcgan",
            help="One of: mlp, cnn, dcgan, resnet",
        )  # try resnet :)
        self.parser.add_argument(
            "--gen_norm",
            type=str,
            default="batchnorm",
            help="One of: None, batchnorm, instancenorm",
        )
        self.parser.add_argument(
            "--ngf",
            type=int,
            default=75,
            help="number of features in the generator network",
        )
        self.parser.add_argument(
            "--nef",
            type=int,
            default=65,
            help="number of features in the generator network",
        )
        self.parser.add_argument(
            "--gen_nextra_layers",
            type=int,
            default=0,
            help="number of extra layers in the generator network",
        )
        self.parser.add_argument(
            "--gen_bias_type", type=str, default=None, help="One of: None, plane"
        )
        self.parser.add_argument("--netG", default="", help="path to netG (to continue training)")
        self.parser.add_argument(
            "--netG2",
            default="",
            help="path to netG2 (normal generator to continue training)",
        )
        self.parser.add_argument(
            "--fix_splat_pos",
            action="store_true",
            default=True,
            help="X and Y coordinates are fix",
        )
        self.parser.add_argument("--zloss", type=float, default=0.0, help="use Z loss")
        self.parser.add_argument(
            "--unit_normalloss", type=float, default=0.0, help="use unit_normal loss"
        )
        self.parser.add_argument(
            "--norm_sph_coord",
            action="store_true",
            default=True,
            help="Use spherical coordinates for the normal",
        )
        self.parser.add_argument(
            "--max_gnorm",
            type=float,
            default=500.0,
            help="max grad norm to which it will be clipped (if exceeded)",
        )
        self.parser.add_argument("--disc_type", type=str, default="cnn", help="One of: cnn, dcgan")
        self.parser.add_argument(
            "--disc_norm",
            type=str,
            default="None",
            help="One of: None, batchnorm, instancenorm",
        )
        self.parser.add_argument(
            "--ndf",
            type=int,
            default=75,
            help="number of features in the discriminator network",
        )
        self.parser.add_argument(
            "--disc_nextra_layers",
            type=int,
            default=0,
            help="number of extra layers in the discriminator network",
        )
        self.parser.add_argument("--nz", type=int, default=100, help="size of the latent z vector")
        self.parser.add_argument("--netD", default="", help="path to netD (to continue training)")
        self.parser.add_argument("--netE", default="", help="path to netD (to continue training)")

        # Optimization parameters
        self.parser.add_argument(
            "--optimizer", type=str, default="adam", help="Optimizer (adam, rmsprop)"
        )
        self.parser.add_argument(
            "--lr", type=float, default=0.0001, help="learning rate, default=0.0002"
        )
        self.parser.add_argument(
            "--lr_sched_type",
            type=str,
            default="step",
            help="Learning rate scheduler type.",
        )
        self.parser.add_argument(
            "--z_lr_sched_step",
            type=int,
            default=100000,
            help="Learning rate schedule for z.",
        )
        self.parser.add_argument(
            "--lr_iter",
            type=int,
            default=10000,
            help="Learning rate operation iterations",
        )
        self.parser.add_argument(
            "--normal_lr_sched_step",
            type=int,
            default=100000,
            help="Learning rate schedule for " "normal.",
        )
        self.parser.add_argument(
            "--z_lr_sched_gamma",
            type=float,
            default=1.0,
            help="Learning rate gamma for z.",
        )
        self.parser.add_argument(
            "--normal_lr_sched_gamma",
            type=int,
            default=1.0,
            help="Learning rate gamma for " "normal.",
        )
        self.parser.add_argument(
            "--alt_opt_zn_interval",
            type=int,
            default=None,
            help="Alternating optimization interval. "
            "[None: joint optimization, 20: every 20 iterations, etc.]",
        )
        self.parser.add_argument(
            "--alt_opt_zn_start",
            type=int,
            default=100000,
            help="Alternating optimization start interaction. [-1: starts immediately,"
            "100: starts alternating after the first 100 iterations.",
        )
        self.parser.add_argument(
            "--normal_consistency_loss_weight",
            type=float,
            default=1e-3,
            help="Normal consistency loss weight.",
        )
        self.parser.add_argument(
            "--z_norm_weight_init",
            type=float,
            default=1e-2,
            help="Normal consistency loss weight.",
        )
        self.parser.add_argument(
            "--z_norm_activate_iter",
            type=float,
            default=1000,
            help="Normal consistency loss weight.",
        )
        self.parser.add_argument(
            "--spatial_var_loss_weight",
            type=float,
            default=1e-2,
            help="Spatial variance loss weight.",
        )
        self.parser.add_argument(
            "--grad_img_depth_loss",
            type=float,
            default=2.0,
            help="Spatial variance loss weight.",
        )
        self.parser.add_argument(
            "--spatial_loss_weight",
            type=float,
            default=0.5,
            help="Spatial smoothness loss weight.",
        )
        self.parser.add_argument(
            "--beta1", type=float, default=0.0, help="beta1 for adam. default=0.5"
        )
        self.parser.add_argument(
            "--n_iter", type=int, default=76201, help="number of iterations to train"
        )
        self.parser.add_argument("--batchSize", type=int, default=4, help="input batch size")

        # GAN parameters
        self.parser.add_argument(
            "--criterion",
            help="GAN Training criterion",
            choices=["GAN", "WGAN"],
            default="WGAN",
        )
        self.parser.add_argument(
            "--gp",
            help="Add gradient penalty",
            choices=["None", "original"],
            default="original",
        )
        self.parser.add_argument("--gp_lambda", help="GP lambda", type=float, default=10.0)
        self.parser.add_argument(
            "--critic_iters", type=int, default=5, help="Number of critic iterations"
        )
        self.parser.add_argument(
            "--clamp", type=float, default=0.01, help="clamp the weights for WGAN"
        )

        # Other parameters
        self.parser.add_argument(
            "--no_cuda", action="store_true", default=False, help="enables cuda"
        )
        self.parser.add_argument("--ngpu", type=int, default=1, help="number of GPUs to use")
        self.parser.add_argument("--manualSeed", type=int, help="manual seed")
        self.parser.add_argument("--out_dir", type=str, default=default_out)
        self.parser.add_argument("--name", type=str, default="", required=False)

        # Camera parameters
        self.parser.add_argument("--width", type=int, default=128)
        self.parser.add_argument("--height", type=int, default=128)
        self.parser.add_argument(
            "--cam_dist",
            type=float,
            default=3.0,
            help="Camera distance from the center of the object",
        )
        self.parser.add_argument("--nv", type=int, default=10, help="Number of views to generate")
        self.parser.add_argument("--angle", type=int, default=30, help="cam angle")
        self.parser.add_argument(
            "--fovy",
            type=float,
            default=30,
            help="Field of view in the vertical direction. Default: 15.0",
        )
        self.parser.add_argument("--focal_length", type=float, default=0.1, help="focal length")
        self.parser.add_argument(
            "--theta",
            nargs=2,
            type=float,
            default=[20, 80],
            help="Angle in degrees from the z-axis.",
        )
        self.parser.add_argument(
            "--phi",
            nargs=2,
            type=float,
            default=[20, 70],
            help="Angle in degrees from the x-axis.",
        )
        self.parser.add_argument(
            "--axis",
            nargs=3,
            default=[0.0, 1.0, 0.0],
            type=float,
            help="Axis for random camera position.",
        )
        self.parser.add_argument("--cam_pos", nargs=3, type=float, help="Camera position.")
        self.parser.add_argument(
            "--at",
            nargs=3,
            default=[0.05, 0.0, 0],
            type=float,
            help="Camera lookat position.",
        )
        # self.parser.add_argument('--at', nargs=3, default=[ 0, 1, 0], type=float, help='Camera lookat position.')
        self.parser.add_argument(
            "--sphere-halfbox", action="store_true", help="Renders demo sphere-halfbox"
        )
        self.parser.add_argument(
            "--norm_depth_image_only",
            action="store_true",
            default=False,
            help="Render on the normalized" " depth image.",
        )
        self.parser.add_argument("--mesh", action="store_true", help="Render as mesh if enabled.")
        self.parser.add_argument(
            "--test_cam_dist",
            action="store_true",
            help="Check if the images are consistent with a" "camera at a fixed distance.",
        )

        # Rendering parameters
        self.parser.add_argument(
            "--splats_img_size",
            type=int,
            default=128,
            help="the height / width of the number of generator splats",
        )
        self.parser.add_argument(
            "--render_type",
            type=str,
            default="img",
            help="render the image or the depth map [img, depth]",
        )
        self.parser.add_argument(
            "--render_img_size",
            type=int,
            default=128,
            help="Width/height of the rendering image",
        )
        self.parser.add_argument(
            "--splats_radius",
            type=float,
            default=0.05,
            help="radius of the splats (fix)",
        )
        self.parser.add_argument(
            "--est_normals",
            action="store_true",
            help="Estimate normals from splat positions.",
        )
        self.parser.add_argument(
            "--same_view", action="store_true", help="data with view fixed"
        )  # before we add conditioning on cam pose, this is necessary
        self.parser.add_argument(
            "--print_interval", type=int, default=10, help="Print loss interval."
        )
        self.parser.add_argument(
            "--save_image_interval", type=int, default=100, help="Save image interval."
        )
        self.parser.add_argument(
            "--save_interval", type=int, default=5000, help="Save state interval."
        )

    def parse(self):
        """Parse."""
        if not self.initialized:
            self.initialize()
        self.opt = self.parser.parse_args()

        # Make output folder
        # try:
        #     os.makedirs(self.opt.out_dir)
        # except OSError:
        #     pass

        # Set render number of channels
        if self.opt.render_type == "img":
            self.opt.render_img_nc = 3
        elif self.opt.render_type == "depth":
            self.opt.render_img_nc = 1
        else:
            raise ValueError("Unknown rendering type")

        # # Set random seed
        # if self.opt.manualSeed is None:
        #     self.opt.manualSeed = random.randint(1, 10000)
        # print("Random Seed: ", self.opt.manualSeed)
        # random.seed(self.opt.manualSeed)
        # torch.manual_seed(self.opt.manualSeed)
        # if not self.opt.no_cuda:
        #     torch.cuda.manual_seed_all(self.opt.manualSeed)

        # # Set number of splats param
        # self.opt.n_splats = self.opt.splats_img_size*self.opt.splats_img_size

        # # Check CUDA is selected
        # cudnn.benchmark = True
        # if torch.cuda.is_available() and self.opt.no_cuda:
        #     print("WARNING: You have a CUDA device, so you should "
        #           "probably run with --cuda")

        return self.opt


param = Parameters()
args = param.parse()

print("\n".join(textwrap.wrap(str(args), width=80)))
# print(args)
expected = """
Namespace(alt_opt_zn_interval=None, alt_opt_zn_start=100000, angle=30, at=[0.05,
0.0, 0], axis=[0.0, 1.0, 0.0], batchSize=4, beta1=0.0,
bg_model='../../../data/halfbox.obj', cam_dist=3.0, cam_pos=None, clamp=0.01,
classes='bowl', criterion='WGAN', critic_iters=5,
dataset='objects_folder_multi', dis_model_path=None, dis_model_path2=None,
disc_nextra_layers=0, disc_norm='None', disc_type='cnn', est_normals=False,
fix_splat_pos=True, focal_length=0.1, fovy=30, full_sphere_sampling=False,
full_sphere_sampling_light=True, gen_bias_type=None, gen_model_path=None,
gen_model_path2=None, gen_nextra_layers=0, gen_norm='batchnorm',
gen_type='dcgan', gp='original', gp_lambda=10.0, grad_img_depth_loss=2.0,
gz_gi_loss=0.0, height=128, light_change=2000, lr=0.0001, lr_iter=10000,
lr_sched_type='step', manualSeed=None, max_gnorm=500.0, mesh=False,
n_iter=76201, name='', ndf=75, nef=65, netD='', netE='', netG='', netG2='',
ngf=75, ngpu=1, no_cuda=False, norm_depth_image_only=False, norm_sph_coord=True,
normal_consistency_loss_weight=0.001, normal_lr_sched_gamma=1.0,
normal_lr_sched_step=100000, nv=10, nz=100, only_background=False,
only_foreground=False, optimizer='adam', out_dir='out', phi=[20, 70],
pixel_samples=1, print_interval=10, random_rotation=True, render_img_nc=3,
render_img_size=128, render_type='img', rescaled=False, root_dir='default',
root_dir1='default', root_dir2='default', root_dir3='default',
root_dir4='default', rotate_foreground=False, same_view=False,
save_image_interval=100, save_interval=5000, spatial_loss_weight=0.5,
spatial_var_loss_weight=0.01, sphere_halfbox=False, splats_img_size=128,
splats_radius=0.05, stoch_enc=False, synsets='', test_cam_dist=False, theta=[20,
80], toy_example=False, unit_normalloss=0.0, use_mesh=True, use_old_sign=True,
use_penality=True, use_quartic=False, width=128, workers=0,
z_lr_sched_gamma=1.0, z_lr_sched_step=100000, z_norm_activate_iter=1000,
z_norm_weight_init=0.01, zloss=0.0)
"""
