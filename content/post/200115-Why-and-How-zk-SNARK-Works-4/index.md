---
title: "从零开始学习 zk-SNARK（四）——多项式的约束"
date: 2020-01-15T08:00:00+08:00
summary: "上一篇文章中我们学习了如何将程序转换为多项式进行证明。到这里似乎已经有点晕了，本文将对协议执行进一步的约束，并对协议展开优化。"
featuredImage: "img/4/WX20200116-211300@2x.png"
slug: "learn zk-SNARK from zero part four"
markup: pandoc
author: Maksym Petkus，翻译 & 注解：even@安比实验室（even@secbit.io）
tags: ["Zero Knowledge Proof", "tutorials", "zkSNARKs"]
categories: ["Zero Knowledge Proof", "zkSNARKs"]
---


> even@安比实验室: 上一篇文章中我们学习了如何将程序转换为多项式进行证明。到这里似乎已经有点晕了，本文将对协议执行进一步的约束，并对协议展开优化。



作者：Maksym Petkus

翻译 & 注解：even@安比实验室（even@secbit.io）

校对：valuka@安比实验室

本系列文章已获作者中文翻译授权。

## 结构性质

上文中的修改额外带来了一些其它有用的性质。

### 静态系数

在上文的构造中，我们通过对 *未赋值的变量多项式* 的计算得到0 或者 1 ，以此表示在运算中是否要用到这个变量。自然地想，我们也可以使用其它系数值，包括负数值，因为我们可以*插值* 计算出经过任何必要的点（前提是没有两个计算使用了同一个 *x*）的多项式。如下是这种运算的一些例子：

$\textcolor{green}{2a} \times \textcolor{blue}{1b} = \textcolor{red}{3r}$

$\textcolor{green}{-3a} \times \textcolor{blue}{1b} = \textcolor{red}{-2r}$

现在我们的程序就可以使用静态系数了，例如：

```pseudocode
Algorithm 2: Constant coefficients
————————————————————————————————————————————————————————————

function calc(w, a, b)
    if w then
        return 3a × b
    else 
        return 5a × 2b
    end if
end function
```

在 setup 阶段这些系数类似于 0 或者 1 将被“硬编码”进去，之后就不能再修改了。现在我们将运算形式修改为：

$\textcolor{green}{c_a \cdot a} \times \textcolor{blue}{c_b \cdot b} = \textcolor{red}{c_r \cdot r}$

或者更正式得用参数 v<sub>n</sub> ∈ {v<sub>1</sub>, v<sub>2</sub>, …, v<sub>n</sub>} 表示：

$\textcolor{green}{c_l \cdot v_l} \times \textcolor{blue}{c_r \cdot v_r} = \textcolor{red}{c_o \cdot v_o}$

其中下标 *l* ，*r* 和 *o* 表示变量在运算中的位置。

*注意：在不同的运算和操作数/输出中，同一个变量的常量系数可以是不同的。*

### 没有成本的做加法

看一下这个新结构，很显然在多项式的表示中，每一个不同 x 所要代表的操作数都是所有*操作数变量多项式* 的总和，其中只有一个被用到的变量是非零值而其它都为 0，下图就很好得表达了这个意思：

![](./img/4/1*HeUXxV8-H5MVbhdT8haqqw.png)

我们可以利用这一个结构，加任何数量必要的*变量* 到每一个运算的操作符/输出中。例如在第一个运算中，我们可以首先做加法 *a+c*，然后就只需要用别的操作数与之相乘了，即 (*a*+ *c*) × *b* = *r*，可以表示为下图：

![](./img/4/1*RpLBxan0och5LvpuE5KJVw.png)

因而也可以将这些变量中任意个，对它们先乘以任意的系数再一并加入到一起作为单个操作数中，以此来根据相应程序的需要构造一个操作数值。这个特性实际上就允许将运算结构改为：

$\textcolor{green}{(c_{1,a} \cdot a + c_{1,b} \cdot b + …) } \times \textcolor{blue}{(c_{r,a} \cdot a + c_{r,b}\cdot b + …)} = \textcolor{red}{(c_{o,a} \cdot a + c_{o,b} \cdot b + …)}$

或者更正式一些用变量  *vᵢ* ∈ {*v*₁*, v*₂*, …, vₙ*} 和操作数变量系数 $c_{l,i} \in \{c_{l,1}, c_{l,2},……,c_{l,n}\}, c_{r,i} \in \{c_{r,1}, c_{r,2},……,c_{r,n}\},c_{o,i} \in \{c_{o,1}, c_{o,2},……,c_{o,n}\},$

这个结构就是：

$\textcolor{green}{\sum_{i=1}^n {c_{l,i} \cdot v_i}} \times \textcolor{blue}{\sum_{i=1}^n {c_{r,i} \cdot v_i}} = \textcolor{red}{\sum_{i=1}^n {c_{o,i} \cdot v_i}}$

*注意 ：每一个运算的操作数都有自己的一组系数 c。*

> even@安比实验室：乘法运算是关键，而加法运算都可以被合并到一个更大的乘法运算里面。



### 加法，减法和除法

到目前为止，我们一直专注于乘法操作。但是为了能够执行通用计算，真实环境下的程序也需要加法，加法和除法。

**加法** 在前面的章节中，我们已经确定了可以在单个操作数的内容中将变量加起来，然后和另一个操作数相乘，即(3*a* + *b*) × *d* = *r* ，但是如果我们只是想做加法，没有乘法，例如一个程序中需要做  a + b 的计算，我们可以按照下面的方式来表示： *(a+b) × 1 = r​*

> @Maksym（作者）：因为我们的结构中对于每一个操作数我们既需要常量系数也需要变量 (c ⋅ v) ，1 这个值可以表示为  c*₁* ⋅ v*₁*，其中  c*₁* = *1* 可以被“硬编码”到对应的多项式中， v*₁* 是一个变量可以给它分配任何值，那么我们就必须通过一些约束来限制 v*₁* 的值，这个在后面的章节中将会讲到。

**减法** 减法与加法几乎一致，唯一的不同就是负系数， a-b也就是：

$\textcolor{green}{(a+-1 \cdot b)} \times \textcolor{blue}{1} = \textcolor{red}{r}$

**除法** 如果我们检查除法运算

$\frac{factor}{divisor} = result$

可以看到除法的结果是就是我们要得到一个结果值使其乘以 divisor 能够得到 factor。所以我们也可以用乘法来表示出同一个意思：*divisor × result = factor*。这样就是说如果我们想要去证明除法运算 *a / b= r*，我们就可以把它表示为：

$\textcolor{green}{b} \times \textcolor{blue}{r} = \textcolor{red}{a}$

> @Maksym（作者）：运算的结构也称为 “约束” ，因为多项式结构代表的运算，并非是为了计算出结果，而是在 prover已经知晓的变量赋值的情况下，检验这个运算的过程是否正确。换句话说，即约束 prover 必须提供一致的值，无论这些值是什么。
>
> 所有的算术计算（加减乘除）都已经有了，于是运算结构不再需要修改。  

> even@安比实验室: 约束和运算有一定的关联性。算术电路的目的是为了实现「计算的验证」，而非「计算的过程」。
>
> 上一篇文章中，我们提出了一种方法：把构造多项式的工作交给 setup 环节，prover 只要填上对应的数值就可以了。 这个方法不仅解决了同一个操作数运算符中不一致的问题，同时还带来了额外的便利：
>
> 1）允许执行计算的表达式中包含静态系数。
>
> 2）虽然l(x)·r(x)=o(x)的关系中只有乘法，但利用这个方法也可以轻松的执行加法操作，继而也就解决了减法和除法的问题。

## 计算示例

有了一组通用的运算结构，我们就可以将我们原始的程序（上一篇文章中的例子）转换成一组运算，然后再转换成多项式的形式。我们先来想一下算法的数学形式（用变量 *v* 表示运算结果）：

$ w \times (a \times b) + (1 - w) \times (a+b) = v$

这里有三个乘法，但是由于运算结构只支持一个乘法操作，所以这里至少就要做三次运算。但是，我们可以将它简化为:

$w \times (a \times b) + a + b -w \times (a + b) = v$

$w \times (a \times b - a - b) = v -a- b$

现在要包含同样的关系只需要两个乘法。这种运算的完整形式就是：

$1: \qquad  \textcolor{green}{1 \cdot a} \times \textcolor{blue}{1 \cdot b }= \textcolor{red}{1 \cdot m} $

$2:  \qquad \textcolor{green}{1 \cdot w} \times \textcolor{blue}{1 \cdot m + -1 \cdot a + -1 \cdot b} = \textcolor{red}{1 \cdot v + -1 \cdot a + -1 \cdot b}$

我们还可以再增加一条约束使 *w* 必须为二进制数，否则 prover 就可以代入任何值去执行一个错误的运算了：

$3：  \qquad \textcolor{green}{1 \cdot w} \times \textcolor{blue}{1 \cdot w}  = \textcolor{red}{1 \cdot w} $

要了解为什么 *w* 只能为 0 或者 1，我们可以把等式表示为 *w*² – *w* = 0，也就是 *(w – 0)(w – 1) = 0* 这里 0 和 1 是唯一解。

现在一共有 5 个变量，以及 2 个左操作符， 4 个右操作符和 5 个输出。操作符多项式为：

$\textcolor{green}{L(x) = a \cdot l_a(x) + w \cdot l_w(x)}$

$\textcolor{blue}{R(x) = m \cdot r_m(x) + a \cdot r_a(x) + b \cdot r_b(x)}$

$\textcolor{red}{O(x) = m \cdot o_m(x) + v \cdot o_v(x) + a \cdot o_a(x) + b \cdot o_b(x)}$

在三次运算中必须为每个*变量多项式 都分别算出一个对应的系数或者如果这个多项式在计算的操作数或者输出中没有被用到的话系数就置为 0。

![](./img/4/eq1.png)

结果因式多项式就是  *t(x) = (x – 1)(x –2)(x –3)*，它必须确保这三个运算都能被正确计算。

接下来，我们利用多项式插值法来找到每个变量多项式：

![](./img/4/eq2.png)


绘制出来就是：

![](./img/4/1*YoNx3JunyKJh8kFad6qtpQ.png)

我们准备通过多项式去证明计算，首先，选择函数的输入值，例如： *w* *= 1*, *a* *= 3*, *b*= 2。其次，计算过程中的中间变量值为：

*m=a × b =6*

*v = w(m-a-b)+a+b=6*

然后，我们把所有计算结果中的值赋值到 *变量多项式* 中，然后相加得到操作数或者输出多项式的形式：

$\textcolor{green}{L(x)}=\textcolor{green}{3 \cdot l_a(x) +1 \cdot l_w(x)} = x^2 -5x+7$

$\textcolor{blue}{R(x)}=\textcolor{blue}{6 \cdot r_m(x) + 3 \cdot r_a(x) + 2 \cdot r_b(x) + 1 \cdot r_w(x)} = \frac{1}{2}x^2 -2 \frac{1}{2}x +4$

$\textcolor{red}{O(x)}=\textcolor{red}{6 \cdot o_m(x) + 6 \cdot o_v(x) + 3 \cdot o_a(x)+ 2 \cdot o_b(x) + 1 \cdot o_w(x)}= 2 \frac{1}{2}x^2 + 12 \frac{1}{2}x +16$

在图中就表示为：

![](./img/4/1*XwRYLT4_4KRPTqQKg2jqfQ.png)

把他们相加成对应运算中的操作数和输出值：

![](./img/4/1*8xEajzq2MlB9i7O8PQ829Q.png)

我们需要去证明  *L*(*x*) × *R*(*x*) – *O*(*x*) = *t*(*x*)*h*(*x*)，因而我们先找出 *h*(*x*)：

$h(x) = \frac{L(x) \times R(x) - O(x)}{t(x)} = \frac{\frac{1}{2}x^4 - 5x^3 + \frac{35}{2}x^2 -25x +12}{(x-1)(x-2)(x-3)} = \frac{1}{2}x - 2$

以图的形式表示为：

![](./img/4/1*z4sW_cYeeGZS_8AAJzfoKQ.png)

这里很明显多项式 *L*(*x*) × *R*(*x*) – *O*(*x*) 的解为 *x*= 1， *x*= 2 和 *x*= 3，因而 *t(x)* 是它的因式，假如使用了和它不一致的变量值，情况就不是这样了。

这就是一组能够正确计算的变量值，如何在多项式层面上证明出来的。下面 prover 还要再继续处理协议的密码学部分。

## 可验证计算协议

我们基于前文中**多项式知识协议** 做了很多重要的修改使它变得更通用，我们再来看一下它现在的定义。假定函数 *f*(*) 是要证明的问题中的计算结果，其中操作数的数量为 *d* ，变量的数量 *n* ，以及它们对应的系数为：

$\{c_{L,i,j},c_{R,i,j},c_{o,i,j}\}_{i \in {1,…,d}, j \in {i,…,d}}$


* Setup

  * 为左操作数 $\{l_i(x)\}_{i \in \{1,…,n\}}$ 构造*变量多项式* 然后对于所有 $j \in \{1,…,d\}$ 的运算都算出其对应的系数，即 $l_i(j) = c_{L,i,j}$，对右操作数和输出也做同样的事情。

  * 随机抽取 *s*，$α$ 

  * 计算 *t(x)= (x-1)(x-2)…(x-d)* 及其结果 $g^{t(s)}$

  * 计算 *proving key*：

    $(\{g^{s^k}\}_{k \in[d]},\{g^{l_i(s)}, g^{r_i(s)}, g^{o_i(s)},g^{αl_i(s)},g^{αr_i(s)},g^{αo_i(s)}\}_{i \in \{1,……,n\}})$

  * 计算 *verification key*：

    $(g^{t(s)},g^α)$

* Proving

  * 计算函数 *f(\*)* 以此计算相应的变量 $\{v_i\}_{i \in \{1,…,n\}}$

  * 计算 $h(x) = \frac{L(x) \times R(x) - O(x)}{t(x)}$，其中 $L(x) = \sum_{i=1}^n {v_i \cdot l_i(x)}$，$R(x)$, $O(x)$ 与之相似

  * 给变量赋值并对操作数多项式求和：

    $g^{L(s)} = (g^{l_1(s)})^{v_1}…(g^{l_n(s)})^{v_n},g^{R(s)} = \prod_{i=1}^n{(g^{r_i(s)})^{v_i}}, g^{O(s)} = \prod_{i=1}^n{(g^{o_i(s)})^{v_i}}$

  * 对变换后的多项式赋值：

    $g^{αL(s)} = \prod_{i=1}^n{(g^{αl_i(s)})^{v_i}},g^{αR(s)} = \prod_{i=1}^n{(g^{αr_i(s)})^{v_i}}, g^{αO(s)} = \prod_{i=1}^n{(g^{αo_i(s)})^{v_i}}$

  * 使用 s 的幂加密值：$\{g^{s^k}\}_{k \in [d]}$ 计算加密值 $g^{h(s)}$

  * 生成证明：$\{g^{L(s)},g^{R(s)},g^{O(s)},g^{αL(s)},g^{αR(s)},g^{αO(s)},g^{h(s)}\}$

* Verification

  * 解析证明为 $\{g^L,g^R,g^O,g^{L'},g^{R'},g^{O'},g^{h}\}$

  * 检查可变多项式约束：

    $e(g^L,g^α) = e(g^{L'},g), e(g^R,g^α) = e(g^{R'},g), e(g^O,g^α)=e(g^{O'},g)$

  * 验证计算有效性：

    $e(g^L,g^R) = e(g^t,g^h) \cdot e(g^O,g)$

*注意：使用符号  ∏ 来表示多个元素连乘，即： $\prod_{i=1}^n{v_i} = v_1 \cdot v_2 \cdot … \cdot v_n$*

对于 *i ∈ {1, …, n}* 所有变量多项式 {*lᵢ*(*x*)*, rᵢ*(*x*)*, oᵢ*(*x*)}  和目标多项式 *t(x)* 的设置被称为一个*二元算术程序* (QAP，在[[Gen+12](#8bfc)] 中有介绍)。

虽然协议足够健壮，可以进行常规的计算验证，但这里依然还有两个安全考虑需要去解决。

### 操作数和输出的不可替代性

因为在 *变量多项式约束检查* 中的所有操作数上我们使用了同一个 *α*，所以就没有办法阻止 prover 做下面的欺骗行为：

* 使用其它的操作数中的可变多项式，即 *L*′(*s*) = *o*₁(*s*) + *r*₁(*s*) + *r*₁(*s*) + *…*
* 完全交换 *操作数多项式*， 也就是把 *O*(*s*) 和 *L*(*s*) 换成  *O(s) × R(s) = L(s)*
* 复用相同的操作数多项式，即  *L(s) × L(s) = O(s)*

可交换性就是指 prover 可以修改计算过程，并有效证明一些其它无关的计算结果。防止这种行为的一个很显然的方式就是在不同的操作数上使用不同的 *α<sub>s</sub>* ，具体协议就可以修改为：

* Setup

  …

  * 选择随机数 $α_l$，$α_r$，$α_o$ 来代替 $α$
  * 计算其对应的“变换” $\{g^{α_ll_i(s)},g^{α_rr_i(s)},g^{α_oo_i(s)}\}_{i \in \{1…n\}}$
  * proving key：$(\{g^{s^k}\}_{k \in [d]},\{g^{l_i(s)}, g^{r_i(s)}, g^{o_i(s)}, g^{α_ll_i(s)}, g^{α_rr_i(s)}, g^{α_oo_i(s)}\}_{i \in \{i…n\}})$
  * verfication key：$(g^{t(s)},g^{α_l},g^{α_r},g^{α_o})$

* Proving

  …

  * 为 “变换”的多项式赋值：$g^{α_lL(s)} = \prod_{i=1}^n{(g^{α_ll_i(s)})^{v_i}}, g^{α_lR(s)} = \prod_{i=1}^n{(g^{α_rr_i(s)})^{v_i}}, g^{α_oO(s)} = \prod_{i=1}^n{(g^{α_oo_i(s)})^{v_i}}$
  * 设置证明：$(g^{L(s)},g^{R(s)},g^{O(s)},g^{α_lL(s)},g^{α_rR(s)},g^{α_oO(s)},g^{h(s)})$

* Verification

  …

  * 可变多项式约束验证：$e(g^L,g^{α_l}) = e(g^{L'},g),e(g^R,g^{α_r}) = e(g^{R'},g),e(g^O,g^{α_o}) = e(g^{O'},g)$

这样就不能在一个操作数中使用其它操作数的变量多项式了，因为 prover 没有办法去获知 $α_l, α_r, α_o$ 来满足 $α_s$ 变换关系。

>even@安比实验室: 这里通过对l(x),r(x)和o(x) 进行分开 KEA 检查，就解决了上篇文章中提出的第二个缺陷问题——由于 prover 生成的证明中只有计算结果，左操作数，右操作数，输出在计算中混用也不会被发现。
>
>同样下面一节也解决了上篇文章中提出的第三个缺陷问题——由于左操作数，右操作数，输出是分开表示的，互相之间的关系无法进行约束。



### 跨操作数的变量一致性

对于任意的变量 vᵢ ，我们都必须将它的值 *分配* 到每个相应操作数中的一个与之对应的*变量多项式* 上，即：

$(g^{l_i(s)})^{v_i}, (g^{r_i(s)})^{v_i},(g^{o_i(s)})^{v_i}$

因为每一个*操作数运算符* 的有效性是分开校验的，并不强制要求我们在对应的*变量多项式* 中使用相同的变量值。这就意味着在左操作数中变量 *v*₁ 的值可以与右操作数或输出中的变量值 *v*₁不同。

我们可以通过熟悉的限制多项式的方法（也就是限制变量多项式的方法）在操作数之间强制变量值相等。如果我们能够在所有的操作数之间创造一个作为“变换的校验和”的变量多项式，那么就可以限制 prover 使其只能够赋予相同的值。verifier 可以将这些每个变量的多项式加起来，即：

$g^{l_i(s)+r_i(s)+o_i(s)}$

然后乘以一个额外的随机数 *β*，即

$g^{β(l_i(s)+r_i(s)+o_i(s))}$

提供这些变换后的多项式给 prover，与变量多项式一起给它赋上变量值：

$(g^{l_i(s)})^{v_{L,i}},(g^{r_i(s)})^{v_{R,i}}, (g^{o_i(s)})^{v_{O,i}}, (g^{β(l_i(s)+r_i(s)+o_i(s))})^{v_{β,i}}$

然后加密 *β* 并把 $g^β$ 加到 *verification key* 中。现在如果所有的 *vᵢ* 值相同，即,

$v_{L,i} = v_{R,i} = v_{o,i} = v_{β,i} \quad 其中  i \in \{1,…,n\}$

等式就满足：

$e(g^{v_{L,i} \cdot l_i(s)} \cdot g^{v_{R,i} \cdot r_i(s)} \cdot g^{v_{o,i} \cdot o_i(s)},g^β)=e(g^{v_{β,i} \cdot β(l_i(s)+r_i(s)+o_i(s))},g)$

尽管这个一致性校验很有用，但还是存在一定的概率  *l*(*s*)*, r*(*s*)*, o*(*s*) 中至少有两项要么计算值相同要么一个多项式可以被另一个整除等情况，这就允许 prover 去分解 $v_{L,i},v_{R,i},v_{O,i},v_{β,i}$ 这些值的关系，使得即使有至少两个不相等的值也依然能够保持等式成立，从而使校验无效：

$(v_{L,i} \cdot l_i(s) + v_{R,i} \cdot r_i(s) + v_{O,i} \cdot o_i(s)) \cdot β = v_{β,i} \cdot β \cdot (l_i(s) + r_i(s) + o_i(s))$

例如，一个以  *l*(*x*) = *r*(*x*) 为例的单个运算。我们用 *w* 来表示这两个值同时  *y* = *o*(*s*)。这个等式看起来就是：

$β(v_Lw + v_Rw+v_Oy) = v_β \cdot β(w+w+y)$

对于任意的 $v_R$ 和 $v_O$，这种形式可以令 $v_β = v_o$，$v_L = 2v_o -v_R$，也就变换成：

$β(2v_ow - v_Rw + v_Rw + v_oy) = v_o \cdot β(2w+y)$

因而这样一个一致性策略是无效的。缓解这种情况的一种方法是对每个操作数都使用不同的 β，确保操作数的*变量多项式* 中包含无法预测的值。以下就是修改后的协议：

* Setup

  * … 随机数 $β_l$， $β_r$， $β_o$

  * 对*变量一致性多项式* 进行计算，加密并添加到 proving key中：

    ${g^{β_ll_i(s)+ β_rr_i(s)+ β_oo_i(s)}}_{i \in \{1,…,n\}}$

  * 对 $β_s$ 加密并将其加到 *verification key* 中：$(g^{β_l},g^{β_r},g^{β_o})$

* Proving

  * …将变量值赋给*变量一致性多项式*：

    $g^{z_i(s)} = (g^{β_ll_i(s)+ β_rr_i(s)+ β_oo_i(s)})^{v_i} \quad for \quad i \in \{1,…,n\}$

  * 增加分配的多项式到加密空间中:

    $g^{Z(s)} = \prod_{i=1}^n{g^{z_i(s)}} = g^{β_lL(s) + β_rR(s)+ β_oO(s)}$

  * 再在证明中加入：$g^{Z(s)}$

* Verification

  * …校验提供的*操作数多项式* 和 “校验和”多项式之间的一致性：

    $e(g^L,g^{β_l}) \cdot e(g^R,g^{β_r}) \cdot e(g^O,g^{β_o}) = e(g^Z,g)$

    这相当于：

    $e(g,g)^{β_lL + β_rR + β_oO} =e(g,g)^Z$

这个构造中同一个变量值就无法乱用了，因为不同的 *β<sub>s</sub>* 使得相同多项式无法兼容，但是这里还存在与  **remark 4.1** 相同的缺陷，由于*g<sup>β<sub>l</sub></sup>*  ，*g<sup>β<sub>r </sub></sup>*， *g<sup>β<sub>o </sub></sup>*是公开可见的，攻击者可以修改任意变量多项式的零索引系数，因为它并不依赖于 *s*，即，*g<sup>β<sub>l</sub>s<sup>0</sup></sup>= g<sup>β<sub>l</sub></sup>*。

> even@安比实验室: 回忆一下，上文中我们提出了在 setup 阶段设置数学表达式的约束关系来解决了一些问题，但这里似乎有引入了一个问题：如果保证 prover 构造的证明是用遵循这些约束关系计算出来的呢？
>
> KEA 其实已经解决了这个问题，但似乎并不完美，这就是我们下面要讨论的变量延展性问题。

### 变量非延展性和变量一致性多项式

**变量多项式的延展性**

举一个  **remark 4.1** 有关的例子，看一下下面的两个运算：

$\textcolor{green}{a} \times \textcolor{blue}{1} = \textcolor{red}{b}$

$\textcolor{green}{3a} \times \textcolor{blue}{1} =\textcolor{red}{c}$

预期的结果 *b = a* 和 *c = 3a* , 再进一步就是  *c = 3b*。这就是说*左操作数的变量* 多项式的计算结果为 l<sub>a</sub>(1) = 1 和 l<sub>a</sub>(2) = 3。先不管  l<sub>a</sub>(*x*) 的形式， prover 都可以不按照上述的比例用另一个修改了的多项式 *lₐ*′(x) = al<sub>a</sub>(x) + 1 来给 *a* 赋值。这样运算就变成了  l<sub>a</sub>′(1) = a+ 1 和 l<sub>a</sub>′(2) = 3*a*+ 1, 结果也就是 *b = a + 1* 和 *c = 3a + 1*，其中 *c≠3b*，这意味着 *a* 的取值的实际意义在不同运算中是不一样的。

但是因为 prover 已经拿到了 *g<sup>α<sub>l</sub></sup>* 和 *g<sup>β<sub>l</sub></sup>* ，所以他依然能够通过正确的操作符多项式* 和*变量值一致性* 的校验：

* …Proving：

  * 用分配不成比例的变量 *a* 来建立左操作数多项式： $L(x) = a \cdot l_a(x) +1$

  * 按照常规的方式构造右操作数多项式和输出多项式： $R(x) = r_1(x), O(x)=b \cdot o_b(x) + c \cdot o_c(x)$

  * 计算除数：$h(x) = \frac{L(x) \cdot R(x) - O(x)}{t(x)}$

  * 计算加密值：$g^{L(s)} = (g^{l_a(s)})^a \cdot g^1$，并按照常规方式计算 $g^{R(s)},g^{O(s)}$

  * 计算 α-变换的加密值：$g^{αL(s)} = (g^{αl_a(s)})^a \cdot g^α$，并按照常规方式计算 $g^{αR(s)},g^{αO(s)}$

  * 计算变量一致性多项式：

    $g^{Z(s)} = \prod_{i \in \{1,a,b,c\}}{(g^{β_ll_i(s)+β_rr_i(s)+β_oO_i(s)})^i \cdot g^{β_l}} = g^{β_l(L(s)+1)+ β_rR(s) +β_oO(s)}$，其中下标 *i* 代表对应变量的符号；指数 *i* 代表变量的值；以及未定义的变量多项式的值为 0。

  * 设置证明：$(g^{L(s)},g^{R(s)},g^{O(s)},g^{α_lL(s)},g^{α_rR(s)},g^{α_oO(s)},g^{Z(s)},g^{h(s)})$

* Verification：

  * 变量多项式约束检查：

    $e(g^L,g^{β_l}) \cdot e(g^R, g^{β_r}) \cdot e(g^O,g^{β_o}) = e(g^Z,g) => e(g,g)^{(a \cdot l_a +1)β_l +Rβ_r + Oβ_o} = e(g,g)^{β_l(L+1)+ β_rR +β_oO}$

  * 有效计算检查：$e(g^L,g^R) = e(g^t,g^h) \cdot e(g^O,g)$

**变量一致性多项式的延展性**

而且 g<sup>β<sub>l</sub></sup>，g<sup>β<sub>r</sub></sup>，g<sup>β<sub>o</sub></sup>的存在允许我们在不同操作数的相同变量上使用不同的值。例如，如果我们有一个运算：

$a \times a = b$

可以用多项式表示：

$l_a(x) = x, r_a(x) = x, o_a(x) = 0$

$l_b(x) = 0, r_b(x) = 0, o_b(x) = x$

尽管我们期待的输出是 *b*= *a*²，但我们可以设置不同的 *a* 值，例如：设置 *a*= 2 （左操作数中）, *a*= 5 （右操作数中）如下：

* Proving：

  * …用 *a=2* 设置左操作数多项式：$L(x) = 2l_a(x) + 10L_b(x)$

  * 用 *a=5* 设置右操作数多项式：$R(x) = 2r_a(x) + 3 + 10r_b(x)$

  * 用 *b=10* 设置输出多项式：$O(x) = 2o_a(x) +10o_b(x)$

  * …计算加密值：

    $g^{L(s)} = (g^{l_a(s)})^2 \cdot (g^{l_b(s)})^{10} = g^{2l_a(s)+10l_b(s)}$

    $g^{R(s)} = (g^{r_a(s)})^2 \cdot (g)^3 \cdot (g^{r_b(s)})^{10} = g^{2r_a(s)+3+10r_b(s)}$

    $g^{O(s)} = (g^{O_a(s)})^2 \cdot (g^{O_b(s)})^{10} = g^{2o_a(s)+10o_b(s)}$

  * 计算变量一致性多项式：

    $g^{Z(s)} = (g^{β_ll_a(s)+β_rr_a(s)+β_oo_a(s)})^2 \cdot (g^{β_r})^3 \cdot (g^{β_ll_b(s)+ β_rr_b(s)+ β_oo_b(s)})^{10} $
    
    $= g^{β_l(2l_a(s)+10l_b(s))+ β_r(2r_a(s)+3+10r_b(s)) + β_o(2o_a(s)+3+10o_b(s))}$

* Verification：

  * ……变量值的一致性检查，应满足：

    $e(g^L,g^{β_l}) \cdot e(g^R, g^{β_r}) \cdot e(g^O,g^{β_o}) = e(g^Z,g)$

注意：多项式 o<sub>a</sub>(x)，l<sub>b</sub>(x)，r<sub>b</sub>(x) 其实可以被忽略掉的，因为这几项对于任何 *x* 的取值，计算结果都为 0，但是为了保持完整性我们依然要保留这几项。



> even@安比实验室：这种能力会危害到协议的可靠性。很显然，加密的 *β*<sub>s</sub>不应该对 Prover 可见。



**非延展性**

解决延展性问题的一个方法就是，在 setup 阶段将 *verification key* 中加密的 β<sub>s</sub> 项与随机秘密值  *γ*(gamma) 相乘使其与加密值 *Z*(*s*) 不兼容：

$g^{β_l \gamma}, g^{β_r\gamma}, g^{β_o\gamma}$

相应的这种被修饰过的加密值，就能阻止使得修改加密值 *Z*(*s*)  变得不可行了，因为 *Z*(*s*) 中没有 *γ*，即：

 $g^{Z(s)} \cdot g^{v' \cdot β_l r} = g^{β_l(L(s)+v'r)+β_rR(s) + β_oO(s)}$

因为变值  *γ*  是随机的 prover 并不知道它的值。所以这个修改就需要我们用 *Z*(*s*) 乘以  *γ* 来平衡协议中的变量值一致性校验* 等式：

* Setup：

  * …随机数 $β_l$，$β_r$，$β_o$，$γ$
  * …设置 *verification key*：$(…, g^{β_l \gamma},  g^{β_r\gamma},  g^{β_o\gamma}, g^{\gamma})$

* Proving：…

* Verification：

  * …变量值一致性检查应满足：

    $e(g^L,g^{β_l\gamma}) \cdot e(g^R,g^{β_r\gamma}) \cdot e(g^O,g^{β_o\gamma}) = e(g^Z, g^{\gamma})$

这里很重要的一点是我们排除了变量多项式为 0-阶的例子（即， *l*₁(*x*) = 1*x*⁰），否则就可以从 *proving key* 的*变量一致性多项式* 中揭露出加了密的 *β* 值

${g^{β_ll_i(s) +β_rr_i(s) + β_oo_i(s)}}_{i \in \{1,…,n\}}$

这个例子中当操作数/输出中的任意两项为 0 时，即，对于 *l*₁(*x*) = 1, *r*₁(*s*) = 0, *o*₁(*s*) = 0 的例子，结果就是

$g^{β_ll_1(s) +β_rr_1(s) +β_oo_1(s)} = g^{β_l}$

我们同样也可以通过*修饰* *α<sub>s</sub>* 项来解决*变量多项式* 的延展性问题。但是这就没有必要了，因为对于*变量多项式* 的任何修改，都需要被映射到变量的*一致性多项式* 中，而一致性多项式是无法修改的。

### 变量值一致性检查的优化

现在*变量值一致性* 检查是有效的，但是这里在 *verification key* 中增加了 4 个昂贵的配对操作和 4 个新的项。文献 [[Par+13](#bd7c)] 中的 Pinocchio 协议用了一个很聪明的方法优化，通过选择不同的生成元 *g* ，从而对每个操作数实行“移位”：

* Setup

  * …选择随机值 $β，γ，\rho_l,\rho_r$ 并设置 $\rho_o = \rho_l \cdot \rho_r$
  * 设置生成元 $g_l=g^{\rho_l}, g_r=g^{\rho_r},g_o=g^{\rho_o}$
  * 设置 *proving key*：$(\{g^{s^k}\}_{k \in [d]},\{g_l^{l_i(s)}, g_r^{r_i(s)}, g_o^{o_i(s)}, g_l^{α_ll_i(s)}, g_r^{α_rr_i(s)}, g_o^{α_oo_i(s)}, g_l^{βl_i(s)}, g_r^{βr_i(s)}, g_o^{βo_i(s)}\}_{i \in [n]})$
  * 设置 *verification key*：$(g_o^{t(s)},g^{α_l},g^{α_r},g^{α_o},g^{βγ}，g^γ)$

* Proving

  * …分配变量值

    $g^{Z(s)} = \prod_{i=1}^n{(g_l^{βl_i(s)} \cdot g_r^{βr_i(s)} \cdot g_o^{βo_i(s)})^{v_i}}$

* Verification

  * …变量多项式约束检查：

    $e(g_l^{L'},g) = e(g_l^L,g^{α_l})$，对 $g_r^{R},g_o^{O}$ 做同样的检查

  * 变量值约束检查：

    $e(g_l^L \cdot g_r^R \cdot g_o^O , g^{βγ}) = e(g^Z,g^γ)$

  * 有效运算检查：

    $e(g_l^L , g_r^R) = e(g_o^t,g^h)e(g_o^O,g) => e(g,g)^{\rho_l\rho_rLR} = e(g,g)^{\rho_l\rho_rth+\rho_l\rho_rO}$

生成元的这种随机化进一步增加了安全性，使得如 **remark 4.1**中描述的*可变多项式* 延展性无效。因为对于故意的修改，它必须要么是*ρ<sub>l</sub>*, *ρ<sub>r</sub>* 或者*ρ<sub>o</sub>* 原始值的倍数要么就是不可直接用的加密值的倍数（假定,如上文所述我们不去处理可能曝光加密后的值的 0 阶可变多项式）。

这个优化使得 *verification key*  减少了两个项，并且去除了 verification 步骤中的两个配对运算。

*注意：在 Jens Groth 2016年的 paper [[Gro16](#2923)] 中有更进一步的改进。*

> even@安比实验室:至此，通用 zk-SNARK 协议的已经几乎构造完成了，本文可以归纳为以下几点：
>
> 协议中是如何增加可变系数的和如何做加减乘除运算的
>
> 协议如何保证操作数和输出的不可替代性
>
> 协议如何保证跨操作数的可变一致性
>
> 协议如何处理非延展性变量和变量一致性
>
> 协议中变量值一致性检查优化



**原文链接**

https://arxiv.org/pdf/1906.07221.pdf

https://medium.com/@imolfar/why-and-how-zk-snark-works-5-variable-polynomials-3b4e06859e30

https://medium.com/@imolfar/why-and-how-zk-snark-works-6-verifiable-computation-protocol-1aa19f95a5cc

**参考文献**

[Par+13] — Bryan Parno, Craig Gentry, Jon Howell, and Mariana Raykova. *Pinocchio: Nearly* *Practical Verifiable Computation*. Cryptology ePrint Archive, Report 2013/279. https://eprint.iacr.org/2013/279. 2013.

[Gen+12] — Rosario Gennaro, Craig Gentry, Bryan Parno, and Mariana Raykova. *Quadratic* *Span Programs and Succinct NIZKs without PCPs*. Cryptology ePrint Archive, Report 2012/215. https://eprint.iacr.org/2012/215. 2012.

[Gro16] — Jens Groth. *On the Size of Pairing-based Non-interactive Arguments*. Cryptology ePrint Archive, Report 2016/260. https://eprint.iacr.org/2016/260. 2016.

#  