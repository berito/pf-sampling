Plan for the report. Agreed text sits under the section it belongs to. Anything marked
NOT WRITTEN YET has nothing agreed in it.

Background comes first and holds everything a reader needs. Section 2 states the two things this
project investigates. Sections 3 and 4 are the work and what it means.


================================================================================
1. BACKGROUND
================================================================================

A robot that must know where it is has two sources of information, and both are unreliable: the
controls it was given, which are corrupted by wheel slip, and the measurements it takes of its
surroundings, which are corrupted by sensor noise. Combining them into an estimate of the pose,
together with an honest account of how uncertain that estimate is, is probabilistic localization.
Doing it while building the map at the same time is SLAM.

Written as a graphical model the problem is a dynamic Bayesian network, and the estimate is the
belief over the latent poses given everything that was observed. The state is continuous and the
measurement model is nonlinear, so the exact algorithms do not apply and the inference has to be
done by sampling. The particle filter represents the belief by a weighted set of samples, which
makes the answer only as good as the sampling that produced it.

That is where the design decisions sit: how new particles are proposed, when the set is resampled,
by which scheme, and how many particles are used. In practice these are inherited from whichever
implementation is at hand, and their effect is rarely measured. This report measures it, in
localization and in SLAM, and then asks whether the noise parameters of the model can be estimated
from the recorded data rather than assumed.

Section 2 gives the background needed to follow the argument, section 3 states the questions this
project addresses, section 4 the method, section 5 the results, and sections 6 and 7 what they
mean.

--------------------------------------------------------------------------------
1.1  Localization and SLAM as a dynamic Bayesian network
--------------------------------------------------------------------------------

Localization and SLAM are state estimation problems. In localization the map is known and the robot
estimates its pose from odometry and observations of known landmarks. In SLAM the map is unknown,
and the robot estimates the map and its own trajectory at the same time.

Both are naturally written as a dynamic Bayesian network. The pose x_t depends on the previous pose
and the control u_t through the motion model p(x_t | x_{t-1}, u_t); each observation z_t depends on
the current pose and the map through the measurement model p(z_t | x_t, m). Controls and
observations are observed, the trajectory is latent, and in SLAM the map is latent as well. The
structure is not something we have to learn: it follows from the robot's kinematics and its sensor
geometry.

--------------------------------------------------------------------------------
1.2  Inference on the network: the Bayes filter, and why no closed form here
--------------------------------------------------------------------------------

Estimation on this network is the Bayes filter, the forward pass of inference on the unrolled
network. The belief p(x_t | z_1:t, u_1:t) is propagated through the motion model and corrected by
the measurement likelihood, one time slice at a time. Because the state is continuous, the belief
is a probability density and the propagation step is an integral over the previous pose. That
integral is tractable in two cases: a discrete state space, where it is a finite sum, and a
linear-Gaussian model, where the belief remains Gaussian and the recursion is the Kalman filter.
Landmark range-bearing measurements are nonlinear in the pose, and under global uncertainty the
belief is multimodal, so neither case applies and no closed form exists.

--------------------------------------------------------------------------------
1.3  The particle filter: likelihood weighting, degeneracy, resampling
--------------------------------------------------------------------------------

The particle filter is the sampling answer to this. Exact inference on the unrolled network is a
forward pass: each time slice sums out the previous pose and multiplies in the evidence. Where that
sum cannot be carried out, it is replaced by samples. Drawing a pose from the motion model and
weighting it by p(z_t | x_t) is likelihood weighting applied to one slice, with the prior as the
proposal distribution, and carrying the weighted set forward to the next slice is what makes it
sequential.

One ingredient has to be added. As the network is unrolled the weights become products of more and
more terms, so they concentrate on a single particle and the set stops representing the belief.
Resampling prevents that, and it is the step with no counterpart in the exact algorithm.

--------------------------------------------------------------------------------
1.4  Rao-Blackwellization and FastSLAM
--------------------------------------------------------------------------------

SLAM adds a second idea. Conditioned on the full trajectory, the landmarks are independent of one
another, which the network shows by d-separation. The posterior therefore factorizes into a
distribution over trajectories and one small estimation problem per landmark, and FastSLAM samples
the trajectory while solving each landmark analytically with an extended Kalman filter. This
Rao-Blackwellization is what makes particle-filter SLAM affordable: the sampled space is the
trajectory, not the trajectory and the whole map.

--------------------------------------------------------------------------------
1.5  Learning the parameters of the network
--------------------------------------------------------------------------------

The models in 2.1 are given, but each carries numbers that somebody has to choose: how much the
wheels slip, how noisy the range and bearing readings are. Write them as theta. Here theta holds
four standard deviations, two for the motion model and two for the measurement model.

Estimating theta from data is parameter learning rather than structure learning. The network is
fixed, and only the numbers inside two of its conditional distributions are unknown. It is learning
with incomplete data, because the trajectory the observations depend on is never seen: the data are
the controls and the observations of a recorded run, and nothing else.

One theta covers the whole run because a dynamic Bayesian network is a template. The same
conditional distribution is instantiated at every time slice, so its parameters are tied across
slices, and each of the T steps is evidence about the same four numbers. A longer trajectory is
more data about theta, not more unknowns.

The estimate is the theta under which the recorded observations are most probable, the maximum of
p(z_1:T | u_1:T, theta). That maximum is in the right place and not merely a convenient one: as the
run grows the average log likelihood tends to a constant minus the Kullback-Leibler divergence
between the true distribution and the model, and that divergence is zero only where the two agree,
so the expected score is largest at the parameters that generated the data.

Computing it meets the obstacle of 2.2 again. The likelihood factorizes into one-step predictive
terms p(z_t | z_1:t-1, theta), each an integral over the pose with no closed form. The particle
filter estimates them as a by-product. With the normalized weights of the previous step and
particles propagated through the motion model, the unnormalized weight of a particle is its
previous weight times p(z_t | x_t, theta), and the sum of those unnormalized weights is the
one-step term: the same sum the filter forms in order to normalize. Adding its logarithm over the
run estimates the log likelihood.

Two consequences follow. The estimate of the likelihood is unbiased, so the estimate of its
logarithm is biased low, and that bias grows as the particle approximation degrades, which makes
the quality of the inference a limit on what can be learned. And the sharpness of the maximum is
the information the data carry about theta, which grows with the number of steps. A parameter the
observations say little about leaves a flat likelihood: it is part of the model and still not
identifiable from the run.


================================================================================
2. THE PROBLEM THIS PROJECT ADDRESSES
================================================================================

The structure of the model is known: it follows from the robot's kinematics and its sensor
geometry, not from the data. What it leaves open is of two kinds.

The first is the inference. The belief admits no closed form, so it is approximated by a sample
set, and the estimate is only as good as that set. A filter must choose a proposal distribution, a
criterion for when to resample, a resampling scheme, and a number of particles. Section 2.1 states
what is tested there.

The second is the parameters of the two conditional distributions: the noise of the motion model
and of the measurement model, which are normally fixed by hand. Whether they can be estimated from
a recorded run, and which of them the data identify at all, is stated in 2.2.

The representation is therefore given; the inference and the parameter learning are what this
project addresses.

--------------------------------------------------------------------------------
2.1  Sampling techniques
--------------------------------------------------------------------------------

The accuracy of the result is therefore governed by the sampling. A filter must choose a proposal
distribution to draw new particles from, a rule for when to resample, a resampling scheme, and a
number of particles. These choices are usually inherited from whatever implementation is at hand.

This project builds a testbed in which those four choices are interchangeable parts of one filter
loop, so that a single choice can be varied while the world, the trajectory and the random seed are
held fixed. The filters themselves are existing open-source implementations: the localization
filters and resampling schemes of Elfring et al., and FastSLAM 1.0 and 2.0 from PythonRobotics.
Each choice is tested in localization and, where it applies, in SLAM.

What is tested:

  the proposal distribution
    - the motion model, which draws from the prior (the bootstrap proposal)
    - the auxiliary particle filter
    - the extended Kalman particle filter
    - FastSLAM 1.0, the motion-model proposal in SLAM
    - FastSLAM 2.0, which draws the pose using the current observation

  when to resample
    - at every step
    - never
    - when the effective sample size falls below a threshold (0.2, 0.5, 0.8)
    - when the largest weight rises above a threshold (0.1, 0.2, 0.5)

  the resampling scheme
    - multinomial
    - residual
    - stratified
    - systematic

  the number of particles
    - 10 to 2500 in localization, 10 and 50 in FastSLAM

--------------------------------------------------------------------------------
2.2  Parameter learning
--------------------------------------------------------------------------------

The report then turns the question around.The noise of the motion and measurement models is
normally set by hand, but those numbers are parameters of the network's two conditional
distributions, and the weights the filter already computes estimate the marginal likelihood of the
observations under them. They can therefore be estimated from a recorded run instead of assumed.
This asks not how well the filter infers under a given model, but which parts of the model the data
can determine at all, and what the inference must be capable of before anything can be determined.

What is tested:
  - whether the noise parameters of the motion and measurement models can be recovered from a
    recorded run
  - which of them the data can determine, and what the inference must be capable of first


================================================================================
3. EXPERIMENTS
================================================================================

--------------------------------------------------------------------------------
3.1  Method: the testbed, the worlds, the metrics, the upstream corrections
--------------------------------------------------------------------------------

The four sampling choices are implemented as interchangeable components of a single filter loop: a
proposal, a criterion for when to resample, a resampling scheme, and an optional move afterwards.
Each is selected by name, so a configuration is a set of names and a particle count, and a new
technique can be added without touching the loop. The same loop serves both problems; what differs
is the state a particle carries, a pose in localization and a pose with its own map in SLAM.

Two simulated worlds are used, both taken unchanged from the reference implementations, so that
each filter is exercised on the problem it was written for.

The localization world is a 10 by 10 m square, cyclic at its edges, with four landmarks. The robot
starts at (7.5, 2) m facing along the y axis and takes 30 steps, each commanding 0.25 m of forward
motion and a turn of 0.02 rad. Its motion noise has standard deviations of 0.005 m and 0.002 rad,
and at every step it measures range and bearing to all four landmarks with noise of 0.2 m and 0.05
rad. The filter is not told the initial pose: particles are drawn uniformly over the world and over
all headings, so the opening steps are global localization. The parameter-learning experiments add
a second setting in which the particles start around the true initial pose, so that the filter
tracks rather than localizes from scratch.

The SLAM world is the FastSLAM scenario of its reference implementation. The robot drives at 1 m/s
with a yaw rate of 0.1 rad/s for 50 s, 500 steps of 0.1 s, among eight landmarks. It observes range
and bearing to every landmark within 20 m, with noise of 0.3 m and 2 degrees, and receives controls
corrupted by noise and by a constant yaw-rate offset. Correspondences are known: every observation
carries the identity of the landmark it measures. All particles start at the true initial pose.

A run is one configuration on one seed. The seed fixes the world, the trajectory and the filter's
randomness, and the same seeds are used for every variant in a comparison, so two variants differ
only in the choice being varied. Every configuration is run on twenty seeds, and every table
reports the mean and the standard deviation over them. A difference is called clear when the 95 per
cent confidence intervals of the two means do not overlap, and within the seed-to-seed spread
otherwise.

What is measured:
  - accuracy: position RMSE, ATE, map error
  - degeneracy: effective sample size, distinct particles after resampling
  - consistency: NEES
  - cost: runtime per step
  - fit: log likelihood of the observations

What is held fixed:
  - the world, the trajectory and the random seed are identical across the variants compared
  - one choice varies at a time
  - twenty seeds per configuration

Reusing an implementation means checking it. Four errors were found in the upstream code, among
them a FastSLAM 2.0 update that never draws from its proposal, and each would have biased the
comparison it appears in.

--------------------------------------------------------------------------------
3.2  Results: the sampling choices
--------------------------------------------------------------------------------

The four choices are taken in turn. Each part states what it varies and what it holds fixed, then
what the result is; the tables and figures carry the numbers.

The resampling scheme. In localization the four schemes are equally accurate: at every particle
count their position errors differ by less than the seed-to-seed spread. They differ clearly in how
many distinct particles survive a resampling step, and in the expected order. With 1000 particles
systematic resampling keeps 72 per cent of them distinct, stratified 67, residual 65 and
multinomial 54, and the same order holds at 50 and 200. In FastSLAM 1.0 that difference reaches the
estimate, because a particle that is lost takes its map with it: with 10 particles systematic
resampling gives an ATE of 0.23 m against 0.32 m for multinomial, and a map error of 0.105 m
against 0.139 m. The runtimes of the four differ by an order of magnitude, but they reflect the
reused implementations rather than the schemes themselves.

When to resample. Not resampling at all triples the error, 1.39 m against roughly 0.46 m. Every
rule that does resample is equally accurate, whether it acts at every step or only when the
effective sample size or the largest weight crosses a threshold. What the thresholds change is how
often resampling happens, between a third of the steps and all of them, not how accurate the filter
is.

The proposal. A proposal that uses the current measurement helps most when particles are scarce.
The auxiliary particle filter is the most accurate localization filter from 100 particles upwards,
0.26 m against 0.46 m for the motion model, and it keeps a far larger effective sample size.
FastSLAM 2.0 builds better maps than FastSLAM 1.0 with 5 to 10 particles. The extended Kalman
particle filter, in the form tested here, does not improve on the motion model and keeps the
smallest effective sample size of the three.

The number of particles. The error falls steeply and then flattens: 1.50 m with 10 particles, 0.46
with 100, 0.16 with 500, 0.13 with 1000 and 0.12 with 2500, while the runtime per step grows
linearly. For this world a few hundred particles give most of the attainable accuracy.

Taken together, the number of particles and the decision to resample at all dominate; the choices
made inside resampling change particle diversity, and that reaches the estimate only where
particles are scarce and each one carries a map.

--------------------------------------------------------------------------------
3.3  Results: parameter learning
--------------------------------------------------------------------------------

Each of the four noise parameters is swept in turn while the other three are held at the values the
world uses, and every value is scored by the log likelihood of the recorded measurements. The
filter uses the motion-model proposal, systematic resampling, an ESS threshold of 0.5 and 2000
particles, and starts around the true initial pose.

The measurement parameters are recovered. The sweeps of the assumed range and bearing noise have a
clear maximum at the true value: 0.19 m against a true 0.2 m, and 0.047 rad against a true 0.05
rad, both within one step of the sweep. The shape on either side is the one the theory predicts.
Too little assumed noise makes the measurements that arrived look impossible and the score falls
steeply; too much makes every pose explain them equally well and the score decays slowly. The
penalty is strongly one-sided: halving the assumed range noise costs about 450 in log likelihood,
quadrupling it about 100. On this world the most plausible setting is also the most accurate one,
so learning the model and tuning for accuracy do not conflict.

The measured curve matches the closed form. For a single Gaussian residual the expected score
relative to its maximum follows from the model, and with four landmarks over 30 steps the range
sweep has 120 such residuals. Nothing is fitted, and the prediction tracks the measurement across
the range: at 0.142, 0.253, 0.45 and 0.8 m it gives -18, -6, -49 and -110 against measured -20, -5,
-47 and -108. The one departure is at the far left, where the prediction is -205 and the
measurement -457, because there the weights degenerate and the downward bias of the estimator takes
over. The agreement shows the sweep measures what it is meant to; the departure marks where the
particle approximation stops being trustworthy.

The motion parameters are not identifiable from 30 steps. Both sweeps are flat, the log likelihood
holding at 205 to 206 while the assumed noise is varied by a factor of 30. The true values, 0.005 m
and 0.002 rad, are small next to the measurement noise the filter corrects with at every step, so
the recorded measurements barely depend on them. This is a property of the data, not of the method:
repeating the turn sweep on 400 steps, with nothing else changed, produces a maximum at the true
value, and an assumed drift ten times too small is then rejected by thousands of nats. Because the
parameters are tied across time slices, the curvature of the likelihood grows with the number of
steps.

Independent recordings agree exactly where the parameter is identifiable. Each seed is a separate
recording, so an estimate can be formed from each one alone. All 20 recordings pick 0.047 rad for
the bearing noise and 17 of 20 pick 0.19 m for the range noise. Where the sweep is flat they do
not: the 20 estimates of the turn noise from 30-step runs are spread over the whole sweep, with no
value chosen by more than a few. On 400 steps they concentrate again. Agreement between recordings
is therefore a usable test of whether a parameter is being estimated at all, and it is also the
test of the tying assumption, since a noise level that changed between runs would scatter even
where the likelihood is sharp.

Learning requires the filter to track. Repeating the range sweep from the uniform start removes the
maximum entirely. With the true, small noise the filter does not find the robot within 30 steps
from a uniform prior: the position error is 2.3 m against 0.063 m from a known start, and the log
likelihood is four orders of magnitude lower. The score then keeps improving as the assumed noise
is widened, because a wider noise lets the particles spread enough to be useful, and only 2 of 20
recordings agree. What the likelihood reports in this regime is which setting lets this filter
work, not which setting generated the data.

The estimate improves with the number of particles and is indifferent to the resampling scheme. At
the true value the estimated log likelihood rises from 28 with a spread of 316 at 25 particles to
205 with a spread of 13 at 2000, and the agreement between recordings rises with it, from none at
25 particles to 17 of 20 at 2000. The four resampling schemes, at 200 particles, all place the
maximum at 0.19 m with 14 or 15 of 20 recordings agreeing.


================================================================================
4. DISCUSSION AND CONCLUSION
================================================================================

Which choices mattered. The number of particles and the decision to resample at all decided most of
the accuracy. The choices made inside resampling decided particle diversity instead, and the two
are not the same thing. The experiments show where the second turns into the first: only when
particles are scarce, and each one carries a map, does a difference in diversity reach the
estimate. The proposal sits between them, mattering most where particles are few and losing its
advantage as they are added.

Trade-offs. A measurement-informed proposal costs more per particle, so the fair comparison is at
equal runtime rather than at equal particle count, and at equal runtime its advantage is much
smaller. Adaptive resampling buys no accuracy in these worlds but saves resampling steps at no
cost; resampling less often leaves each step with more degenerate weights and fewer distinct
particles afterwards, so the threshold trades cost against impoverishment.

What limits learning. There are two limits, of different kinds. The first is the inference. The
objective is estimated by the same weights that do the filtering, so a filter that has not found
the robot reports which setting lets it work rather than which setting generated the data, and a
filter with too few particles reports noise. Inference quality is a precondition for learning, not
merely something that learning improves. The second is the data. The two motion parameters are
perfectly well defined and undetermined by 30 steps of this world, and become determined only when
the trajectory is long enough for their effect to show against the measurement noise; no amount of
computation removes that. Agreement between independent recordings separates the two cases cheaply.

The shape of the likelihood also explains a common practice. Understating a noise level is
penalized far more heavily than overstating it, so values chosen by hand are rationally kept large,
which is what the reused implementations do.

On reusing implementations. Four errors in the upstream code would each have biased a comparison,
one of them turning FastSLAM 2.0 into a second motion-model filter. Comparing reused code requires
checking it first, function by function, against the original.

Limitations. The worlds are small and simulated, with known correspondences. Each experiment varies
one choice while the others are fixed, so interactions between choices are not measured. The
learning experiments estimate one parameter at a time, from a known start, so they do not say what
the joint maximum over all four would be, and a sweep is a cruder optimizer than expectation
maximization.

Conclusion. Written as a dynamic Bayesian network, localization and SLAM make the same three
demands as any graphical model: a structure that justifies a factorization, an inference procedure
for what the structure leaves open, and parameters that have to come from somewhere. This project
took the structure as given and worked on the other two. On the inference side it measured which
sampling choices change the answer, and found that most of the accuracy is decided before the
resampling scheme is chosen. On the learning side it estimated the model's own noise parameters
from recorded runs, recovered the measurement noise, and showed that the motion noise is
identifiable only with more data. The two sides meet in one result: the quality of the approximate
inference sets the ceiling on what can be learned.
