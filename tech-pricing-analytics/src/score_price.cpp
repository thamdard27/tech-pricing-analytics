// score_price.cpp
// -------------------------------------------------------------------
// A small, dependency-free C++ price scorer.
//
// It loads the linear pricing model exported by src/05_export_model.py
// (models/price_model_coeffs.txt) and predicts the USD price of a laptop
// configuration passed on the command line. The Python side experiments and
// trains; this C++ tool is the kind of fast, portable scorer you would deploy
// in a service. Run with no args to score the sample config and print the
// value Python expects, so the two implementations can be checked against
// each other.
//
// Build:   g++ -O2 -std=c++17 -o bin/score_price src/score_price.cpp
// Usage:   ./bin/score_price ram_gb ssd_gb ppi cpu_ghz weight_kg screen_in has_ssd
// Example: ./bin/score_price 16 512 157 2.8 1.6 15.6 1
// -------------------------------------------------------------------
#include <cmath>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

// Feature order must match src/05_export_model.py
static const std::vector<std::string> FEATURES = {
    "ram_gb", "ssd_gb", "ppi", "cpu_ghz", "weight_kg", "screen_in", "has_ssd"};

// Load "key value" lines into a map. Returns false on failure.
bool load_coeffs(const std::string& path, std::map<std::string, double>& out) {
    std::ifstream in(path);
    if (!in) return false;
    std::string key;
    double val;
    while (in >> key >> val) out[key] = val;
    return !out.empty();
}

double predict(const std::map<std::string, double>& coef,
               const std::map<std::string, double>& feats) {
    double log_price = coef.at("intercept");
    for (const auto& f : FEATURES) {
        log_price += coef.at(f) * feats.at(f);
    }
    return std::exp(log_price);  // model is on log(price)
}

int main(int argc, char** argv) {
    std::map<std::string, double> coef;
    if (!load_coeffs("models/price_model_coeffs.txt", coef)) {
        std::cerr << "Could not read models/price_model_coeffs.txt. "
                     "Run: python src/05_export_model.py first.\n";
        return 1;
    }

    std::map<std::string, double> feats;
    if (argc == 1 + (int)FEATURES.size()) {
        // read features from the command line
        for (size_t i = 0; i < FEATURES.size(); ++i)
            feats[FEATURES[i]] = std::stod(argv[i + 1]);
    } else {
        // no args: score the sample config from models/sample_config.txt
        std::ifstream in("models/sample_config.txt");
        if (!in) {
            std::cerr << "No args and no models/sample_config.txt found.\n";
            return 1;
        }
        std::string key;
        double val;
        double py_pred = -1;
        while (in >> key >> val) {
            if (key == "python_predicted_usd") py_pred = val;
            else feats[key] = val;
        }
        double cpp_pred = predict(coef, feats);
        std::cout.setf(std::ios::fixed);
        std::cout.precision(2);
        std::cout << "C++ predicted price:    $" << cpp_pred << "\n";
        if (py_pred > 0) {
            std::cout << "Python predicted price: $" << py_pred << "\n";
            std::cout << "Difference:             $" << std::abs(cpp_pred - py_pred) << "\n";
        }
        return 0;
    }

    double price = predict(coef, feats);
    std::cout.setf(std::ios::fixed);
    std::cout.precision(2);
    std::cout << "Predicted price: $" << price << "\n";
    return 0;
}
