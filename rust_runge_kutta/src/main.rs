const G: f64 = 9.81;
const DT: f64 = 1e-2;

fn derivs(r: [f64; 2], _t: f64) -> [f64; 2] {
    return [r[1], -G]
}

fn rk4(r: &[f64; 2], t: &f64) -> [f64; 2] {
    let k1 = derivs([r[0], r[1]], *t);
    let k2 = derivs([r[0] + k1[0] * DT / 2.0, r[1] + k1[1] * DT / 2.0], t + DT / 2.0);
    let k3 = derivs([r[0] + k2[0] * DT / 2.0, r[1] + k2[1] * DT / 2.0], t + DT / 2.0);
    let k4 = derivs([r[0] + k3[0] * DT, r[1] + k3[1] * DT], t + DT);
    return [
        (k1[0] + 2.0 * k2[0] + 2.0 * k3[0] + k4[0]) * DT / 6.0,
        (k1[1] + 2.0 * k2[1] + 2.0 * k3[1] + k4[1]) * DT / 6.0
    ]
}

fn main() {
    let mut r: [f64; 2] = [0.0, 10.0];
    let mut t: f64 = 0.0;

    while t < 2.0 {
        println!("X: {:.2}  VX: {:.2}", r[0], r[1]);
        let dr = rk4(&r, &t);
        r = [
            r[0] + dr[0],
            r[1] + dr[1]
        ];
        t += DT;
    }
}
