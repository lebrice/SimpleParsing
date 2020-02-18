"""Parameters module."""
import argparse
import simple_parsing
import os
import random
# import getpass
# import torch
# import torch.nn.parallel
# import torch.backends.cudnn as cudnn
# import torch.utils.data
from dataclasses import dataclass, field
from typing import *

from simple_parsing import choice

@dataclass
class DatasetParams:
    """ Dataset Parameters """
    default_root: ClassVar[str] = "/dataset" # the default root directory to use.
    
    dataset: str = 'objects_folder_multi' #laptop,pistol
    """ dataset name: [shapenet, objects_folder, objects_folder]') """
    
    root_dir: str  = default_root # dataset root directory
    root_dir1: str = default_root # dataset root directory
    root_dir2: str = default_root # dataset root directory
    root_dir3: str = default_root # dataset root directory
    root_dir4: str = default_root # dataset root directory

    synsets: str = ''               # Synsets from the shapenet dataset to use
    classes: str = 'bowl'           # Classes from the shapenet dataset to use #,cap,can,laptop
    workers: int = 0                # number of data loading workers
    light_change: int = 2000        # number of data loading workers

    toy_example: bool = False       # Use toy example
    use_old_sign: bool = True       # Use toy example
    use_quartic: bool = False       # Use toy example
    rescaled: bool = False          # Use toy example
    full_sphere_sampling: bool = False    # Use toy example
    full_sphere_sampling_light: bool = True # Use toy example
    random_rotation: bool = True            # Use toy example
    stoch_enc: bool = False                 # Use toy example
    only_background: bool = False           # Use toy example
    only_foreground: bool = False           # Use toy example
    rotate_foreground: bool = False         # Use toy example
    use_penality: bool = True               # Use toy example
    use_mesh: bool = True                   # Render dataset with meshes
    
    gen_model_path:  Optional[str] = None   # 'dataset root directory
    gen_model_path2: Optional[str] = None   # dataset root directory
    dis_model_path:  Optional[str] = None   # dataset root directory
    dis_model_path2: Optional[str] = None   # dataset root directory
    bg_model: str = "../../../data/halfbox.obj" # Background model path
    
    gz_gi_loss: float = 0.0     # grad z and grad img consistency.
    pixel_samples: int = 1      # Samples per pixel.


@dataclass
class NetworkParams:
     # Network parameters
    gen_type: str = choice("dcgan", "mlp", "cnn", "resnet", default="dcgan")    # One of: mlp, cnn, dcgan, resnet # try resnet :)
    gen_norm: str = choice("batchnorm", "instancenorm", default="batchnorm")    # One of: None, batchnorm, instancenorm
    ngf: int = 75                   # number of features in the generator network
    nef: int = 65                   # number of features in the generator network
    gen_nextra_layers: int = 0      # number of extra layers in the generator network
    gen_bias_type: Optional[str] = choice(None, "plane", default=None) # One of: None, plane
    netG: str = ''                  # path to netG (to continue training)
    netG2: str = ''                 # path to netG2 (normal generator to continue training)
    fix_splat_pos: bool = True      # X and Y coordinates are fix
    zloss: float = 0.0              # use Z loss
    unit_normalloss: float = 0.0    # use unit_normal loss
    norm_sph_coord: bool = True     # Use spherical coordinates for the normal
    max_gnorm: float = 500.         # max grad norm to which it will be clipped (if exceeded)
    disc_type: str = choice("cnn", "dcgan", default="cnn") # One of: cnn, dcgan
    disc_norm: str = choice("None", "batchnorm", "instancenorm", default="None") # One of: None, batchnorm, instancenorm
    ndf: int = 75                   # number of features in the discriminator network
    disc_nextra_layers: int = 0     # number of extra layers in the discriminator network
    nz: int = 100   # size of the latent z vector
    netD: str = ''  # path to netD (to continue training)
    netE: str = ''  # path to netD (to continue training)


@dataclass
class OptimizerParams:
    """ Optimization parameters """
    optimizer: str = 'adam'             # Optimizer (adam, rmsprop)
    lr: float = 0.0001                  # learning rate, default=0.0002
    lr_sched_type: str = 'step'         # Learning rate scheduler type.
    z_lr_sched_step: int = 100000       # Learning rate schedule for z.
    lr_iter: int = 10000                # Learning rate operation iterations
    normal_lr_sched_step: int = 100000  # Learning rate schedule for normal.
    z_lr_sched_gamma: float = 1.0       # Learning rate gamma for z.
    normal_lr_sched_gamma: float = 1.0    # Learning rate gamma for normal.
    normal_consistency_loss_weight: float = 1e-3 # Normal consistency loss weight.
    z_norm_weight_init: float = 1e-2        # Normal consistency loss weight.
    z_norm_activate_iter: float = 1000      # Normal consistency loss weight.
    spatial_var_loss_weight: float = 1e-2   # Spatial variance loss weight.
    grad_img_depth_loss: float = 2.0        # Spatial variance loss weight.
    spatial_loss_weight: float = 0.5        # Spatial smoothness loss weight.
    beta1: float = 0.0      # beta1 for adam. default=0.5
    n_iter: int = 76201     # number of iterations to train
    batchSize: int = 4      # input batch size
    alt_opt_zn_interval: Optional[int] = None
    """ Alternating optimization interval.
    - None: joint optimization
    - 20: every 20 iterations, etc.
    """
    alt_opt_zn_start: int = 100000
    """Alternating optimization start interation.
    - -1: starts immediately,
    - '100: starts alternating after the first 100 iterations.
    """

@dataclass
class GanParams:
    """ Gan parameters """
    criterion: str = choice('GAN', 'WGAN', default="WGAN")  # GAN Training criterion
    gp: str = choice("None", 'original', default="original")  # Add gradient penalty
    gp_lambda: float = 10.  # GP lambda
    critic_iters: int = 5   # Number of critic iterations
    clamp: float = 0.01     # clamp the weights for WGAN


@dataclass
class OtherParams:
    """ Other parameters """
    manualSeed: int = 1# manual seed
    no_cuda: bool = False # enables cuda
    ngpu: int = 1 # number of GPUs to use
    out_dir: str = "default_output"
    name: str = ''


@dataclass
class CameraParams:
    """Camera Parameters"""
    cam_pos: Tuple[float, float, float] = (0., 0., 0.)# Camera position.
    width: int = 128
    height: int = 128
    cam_dist: float = 3.0   # Camera distance from the center of the object
    nv: int = 10            # Number of views to generate
    angle: int = 30         # cam angle
    fovy: float = 30        # Field of view in the vertical direction.
    focal_length: float = 0.1 # focal length
    theta:  Tuple[float, float] = (20, 80) # Angle in degrees from the z-axis.
    phi:    Tuple[float, float] = (20, 70) # Angle in degrees from the x-axis.
    axis:   Tuple[float, float, float] = (0., 1., 0.) # Axis for random camera position.
    at:     Tuple[float, float, float] = (0.05, 0.0, 0.0) # Camera lookat position.
    sphere_halfbox: bool = False        # Renders demo sphere-halfbox
    norm_depth_image_only: bool = False # Render on the normalized depth image.
    mesh: bool = False          # Render as mesh if enabled.
    test_cam_dist: bool = False # Check if the images are consistent with a camera at a fixed distance.


@dataclass
class RenderingParams:
    splats_img_size: int = 128  # the height / width of the number of generator splats
    render_type: str = 'img'    # render the image or the depth map [img, depth]
    render_img_size: int = 128  # Width/height of the rendering image
    splats_radius: float = 0.05 # radius of the splats (fix)
    est_normals: bool = False   # Estimate normals from splat positions.
    n_splats: Optional[int] = None
    same_view: bool = False # before we add conditioning on cam pose, this is necessary
    """ data with view fixed """
    
    print_interval: int = 10        # Print loss interval.
    save_image_interval: int = 100  # Save image interval.
    save_interval: int = 5000       # Save state interval.


@dataclass
class Parameters:
    """base options."""
    # Dataset parameters.
    dataset: DatasetParams = DatasetParams()
    # Set of parameters related to the optimizer.
    optimizer: OptimizerParams = OptimizerParams()
    # GAN Settings 
    gan: GanParams = GanParams()
    # Camera settings
    camera: CameraParams = CameraParams()
    # Rendering-related settings
    rendering: RenderingParams = RenderingParams()
    # other (misc) settings
    other: OtherParams = OtherParams()

    def __post_init__(self):
        """ Post-initialization code """
        # Make output folder
        # try:
        #     os.makedirs(self.other.out_dir)
        # except OSError:
        #     pass

        # Set render number of channels
        if self.rendering.render_type == 'img':
            self.rendering.render_img_nc = 3
        elif self.rendering.render_type == 'depth':
            self.rendering.render_img_nc = 1
        else:
            raise ValueError('Unknown rendering type')

        # # Set random seed
        # if self.other.manualSeed is None:
        #     self.other.manualSeed = random.randint(1, 10000)
        # print("Random Seed: ", self.other.manualSeed)
        # random.seed(self.other.manualSeed)
        # torch.manual_seed(self.other.manualSeed)
        # if not self.other.no_cuda:
        #     torch.cuda.manual_seed_all(self.other.manualSeed)

        # # Set number of splats param
        # self.rendering.n_splats = self.rendering.splats_img_size ** 2
        
        # # Check CUDA is selected
        # cudnn.benchmark = True
        # if torch.cuda.is_available() and self.other.no_cuda:
        #     print("WARNING: You have a CUDA device, so you should "
        #           "probably run with --cuda")

    @classmethod
    def parse(cls):
        parser = simple_parsing.ArgumentParser()
        parser.add_arguments(cls, dest="parameters")
        args = parser.parse_args()
        instance: Parameters = args.parameters
        return instance

params = Parameters.parse()
print(params)