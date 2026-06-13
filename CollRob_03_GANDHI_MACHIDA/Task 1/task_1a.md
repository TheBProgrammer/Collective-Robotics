# Task 1a: Derivation of Intersection Probability and Estimation of $\pi$

To derive the intersection probability $P$ for Buffon's Needle, we define the state of a dropped needle using two continuous random variables:
* $x$: The shortest distance from the center of the needle to the nearest parallel line.
* $\theta$: The acute angle between the needle and the parallel lines.

Given the needle length $L$ and line spacing $D$ (where $L \le D$), we can establish the bounds for our sample space:
* Since $x$ is the distance to the *nearest* line, its maximum value is half the distance between two lines: $0 \le x \le \frac{D}{2}$.
* Since $\theta$ represents the acute angle relative to the lines, its range is: $0 \le \theta \le \frac{\pi}{2}$.

### 1. The Total Sample Space
Assuming the needle drops randomly, $x$ and $\theta$ follow a uniform continuous distribution. The total area of all possible outcomes (the sample space) is represented by a rectangle formed by their maximum bounds:
$$\text{Area}_{\text{total}} = \frac{D}{2} \times \frac{\pi}{2} = \frac{D\pi}{4}$$

### 2. The Intersection Condition
A needle intersects a line if the distance from its center to the line ($x$) is less than or equal to the vertical distance from its center to its tip. 

Using basic trigonometry, the vertical distance from the center to the tip is $\frac{L}{2} \sin \theta$. Therefore, an intersection occurs when:
$$x \le \frac{L}{2} \sin \theta$$

### 3. Deriving the Probability $P$
To find the area of "successful" outcomes where an intersection occurs, we integrate the intersection condition over the entire range of valid angles:
$$\text{Area}_{\text{success}} = \int_{0}^{\frac{\pi}{2}} \frac{L}{2} \sin \theta \, d\theta$$

Evaluating this integral yields:
$$\text{Area}_{\text{success}} = \frac{L}{2} \Big[-\cos \theta \Big]_{0}^{\frac{\pi}{2}}$$
$$\text{Area}_{\text{success}} = \frac{L}{2} \left(-\cos\left(\frac{\pi}{2}\right) - (-\cos(0))\right)$$
$$\text{Area}_{\text{success}} = \frac{L}{2} (0 + 1) = \frac{L}{2}$$

The probability $P$ of a needle crossing a line is the ratio of the successful area to the total sample space area:
$$P = \frac{\text{Area}_{\text{success}}}{\text{Area}_{\text{total}}} = \frac{\frac{L}{2}}{\frac{D\pi}{4}}$$

Simplifying the fraction, we get the final intersection probability:
$$P = \frac{2L}{D\pi}$$

---

### Estimating $\pi$

The formula derived above explicitly relates the probability of a needle drop intersecting a line to the constant $\pi$. By rearranging the equation algebraically, we can solve for $\pi$:
$$\pi = \frac{2L}{DP}$$

To estimate $\pi$ experimentally, we can run a simulation where we drop the needle $n$ times and record the total number of line crossings, $C$. According to the law of large numbers, the experimental probability can be approximated as:
$$P \approx \frac{C}{n}$$

By substituting this experimental probability back into our rearranged formula, we obtain an estimator for $\pi$:
$$\pi \approx \frac{2L \cdot n}{D \cdot C}$$