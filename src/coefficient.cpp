#include <iostream>
#include <unordered_map>
#include <stdexcept>

enum class Sex
{
    M,
    F
};

class abc_Widmark
{
public:
    virtual ~abc_Widmark() = default;
    virtual double forward_F(double H, double W, double g) const = 0;
    virtual double forward_M(double H, double W, double g) const = 0;
    double operator()(Sex sex, double H, double W, double g) const
    {
        if (sex == Sex::F)
        {
            return forward_F(H, W, g);
        }
        else if (sex == Sex::M)
        {
            return forward_M(H, W, g);
        }
        else
        {
            throw std::invalid_argument("Invalid sex");
        }
    }
};

class Widmark : public abc_Widmark
{
public:
    double forward_F(double, double, double) const override
    {
        return 0.55;
    }

    double forward_M(double, double, double) const override
    {
        return 0.68;
    }
};

class Watson : public abc_Widmark
{
public:
    double forward_F(double H, double W, double g) const override
    {
        return 0.29218 + (12.666 * H - 2.4846) / W;
    }

    double forward_M(double H, double W, double g) const override
    {
        return 0.39834 + (12.725 * H - 0.11275 * g + 2.8993) / W;
    }
};

class Forrest : public abc_Widmark
{
public:
    double forward_F(double H, double W, double) const override
    {
        return 0.8736 - 0.0124 * W / (H * H);
    }

    double forward_M(double H, double W, double) const override
    {
        return 1.0178 - 0.012127 * W / (H * H);
    }
};

class Seidl : public abc_Widmark
{
public:
    double forward_F(double H, double W, double) const override
    {
        return 0.31223 - 0.006446 * W + 0.4466 * H;
    }

    double forward_M(double H, double W, double) const override
    {
        return 0.31608 - 0.004821 * W + 0.4632 * H;
    }
};

class Ulrich : public abc_Widmark
{
public:
    double forward_F(double, double, double) const override
    {
        throw std::invalid_argument("No estimator available");
    }

    double forward_M(double H, double W, double) const override
    {
        return 0.715 - 0.00462 * W + 0.22 * H;
    }
};

class Average : public abc_Widmark
{
public:
    double forward_F(double H, double W, double g) const override
    {
        return 0.50766 + 0.11165 * H - W * (0.001612 + 0.0031 / (H * H)) - (1 / W) * (0.62115 - 3.1665 * H);
    }

    double forward_M(double H, double W, double g) const override
    {
        return 0.62544 + 0.13664 * H - W * (0.00189 + 0.002425 / (H * H)) + (1 / W) * (0.57986 + 2.545 * H - 0.02255 * g);
    }
};

int main()
{
    Widmark widmark;
    Watson watson;
    Forrest forrest;
    Seidl seidl;
    Ulrich ulrich;
    Average average;

    double H = 170.0; // Replace with actual values
    double W = 70.0;  // Replace with actual values
    double g = 18.0;  // Replace with actual values

    std::cout << "Widmark (F): " << widmark(Sex::F, H, W, g) << std::endl;
    std::cout << "Widmark (M): " << widmark(Sex::M, H, W, g) << std::endl;

    std::cout << "Watson (F): " << watson(Sex::F, H, W, g) << std::endl;
    std::cout << "Watson (M): " << watson(Sex::M, H, W, g) << std::endl;

    std::cout << "Forrest (F): " << forrest(Sex::F, H, W, g) << std::endl;
    std::cout << "Forrest (M): " << forrest(Sex::M, H, W, g) << std::endl;

    std::cout << "Seidl (F): " << seidl(Sex::F, H, W, g) << std::endl;
    std::cout << "Seidl (M): " << seidl(Sex::M, H, W, g) << std::endl;

    try
    {
        std::cout << "Ulrich (F): " << ulrich(Sex::F, H, W, g) << std::endl;
    }
    catch (const std::invalid_argument &e)
    {
        std::cout << "Ulrich (F): " << e.what() << std::endl;
    }

    std::cout << "Ulrich (M): " << ulrich(Sex::M, H, W, g) << std::endl;

    std::cout << "Average (F): " << average(Sex::F, H, W, g) << std::endl;
    std::cout << "Average (M): " << average(Sex::M, H, W, g) << std::endl;

    return 0;
}
