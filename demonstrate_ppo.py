import argparse, sys
import os.path as osp

from env_frontend import MantsinenBasic
from common.server_utils import is_server_running
from time import sleep
from baselines.ppo2.ppo2 import PPO2 as ppo
from common.mevea_vec_env import MeveaVecEnv
from common.data_utils import prepare_trajectories
from config import *

def make_env(env_class, *args):
    fn = lambda: env_class(*args)
    return fn

if __name__ == '__main__':

    # process arguments

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--trajectory', help='Trajectory file.', default='trajectory1.csv')
    parser.add_argument('-c', '--checkpoint', help='Checkpoint file.', default='models/mevea/mantsinen/ppo/model_checkpoints/rl_model_4677632_steps.zip')
    parser.add_argument('-C', '--checkpoints', help='Checkpoint files.', default=[
        'models/mevea/mantsinen/ppo/model_checkpoints/rl_model_0_steps.zip',
        'models/mevea/mantsinen/ppo/model_checkpoints/rl_model_10010624_steps.zip',
        'models/mevea/mantsinen/ppo/model_checkpoints/rl_model_20004864_steps.zip',
        'models/mevea/mantsinen/ppo/model_checkpoints/rl_model_30015488_steps.zip',
        'models/mevea/mantsinen/ppo/model_checkpoints/rl_model_39108608_steps.zip',
        'models/mevea/mantsinen/ppo/model_checkpoints/rl_model_50003968_steps.zip',
        'models/mevea/mantsinen/ppo/model_checkpoints/rl_model_60002304_steps.zip',
        'models/mevea/mantsinen/ppo/model_checkpoints/rl_model_70000640_steps.zip',
        'models/mevea/mantsinen/ppo/model_checkpoints/rl_model_78594048_steps.zip',
    ])
    args = parser.parse_args()

    if args.checkpoint is None and args.checkpoints is None:
        sys.exit(1)

    # check that server is running

    while not is_server_running(server):
        print('Start the server: python3 env_server.py')
        sleep(sleep_interval)

    # extract waypoints

    trajectory_file = osp.join(trajectory_dir, args.trajectory)
    _, _, waypoints = prepare_trajectories(signal_dir, [trajectory_file], use_inputs=use_inputs, use_outputs=use_outputs, action_scale=action_scale, lookback=lookback)

    # create environment

    env_fns = [make_env(
        MantsinenBasic,
        model_path,
        model_dir,
        signal_dir,
        server,
        data,
        nsteps,
        lookback,
        use_inputs,
        use_outputs,
        action_scale,
        tstep
    ) for data in waypoints]
    env = MeveaVecEnv(env_fns)

    # checkpoints

    if args.checkpoints is not None:
        checkpoints = args.checkpoints
    else:
        checkpoints = [args.checkpoint]

    # load model and run it in demo mode for each checkpoint

    for checkpoint in checkpoints:
        try:
            model = ppo.load(checkpoint)
            model.set_env(env)
            print('Model has been successfully loaded from {0}'.format(checkpoint))
            assert checkpoint.endswith('.zip')
            cp_name = osp.basename(checkpoint)
            output_fname = '{0}.mp4'.format(cp_name.split('.zip')[0])
            output = osp.join(video_output, 'ppo', output_fname)
            print('Recording to {0}'.format(output))
            model.demo(output)
        except Exception as e:
            print(e)
            break