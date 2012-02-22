// Generated by the Manycore Form Compiler.
// https://github.com/gmarkall/manycore_form_compiler




void rhs(double localTensor[3], double dt, double c0[3][2], double c1[3], double c2[3][2])
{
  const double CG1[3][6] = { {  0.09157621, 0.09157621, 0.81684757,
                               0.44594849, 0.44594849, 0.10810302 },
                             {  0.09157621, 0.81684757, 0.09157621,
                               0.44594849, 0.10810302, 0.44594849 },
                             {  0.81684757, 0.09157621, 0.09157621,
                               0.10810302, 0.44594849, 0.44594849 } };
  const double d_CG1[3][6][2] = { { {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. } },

                                  { {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. } },

                                  { { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. } } };
  const double w[6] = {  0.05497587, 0.05497587, 0.05497587, 0.11169079,
                         0.11169079, 0.11169079 };
  double c_q1[6];
  double c_q0[6][2][2];
  double c_q2[6][2];
  for(int i_g = 0; i_g < 6; i_g++)
  {
    c_q1[i_g] = 0.0;
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      c_q1[i_g] += c1[i_r_0] * CG1[i_r_0][i_g];
    };
    for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
    {
      for(int i_d_1 = 0; i_d_1 < 2; i_d_1++)
      {
        c_q0[i_g][i_d_0][i_d_1] = 0.0;
        for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
        {
          c_q0[i_g][i_d_0][i_d_1] += c0[i_r_0][i_d_0] * d_CG1[i_r_0][i_g][i_d_1];
        };
      };
    };
    for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
    {
      c_q2[i_g][i_d_0] = 0.0;
      for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
      {
        c_q2[i_g][i_d_0] += c2[i_r_0][i_d_0] * CG1[i_r_0][i_g];
      };
    };
  };
  for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
  {
    localTensor[i_r_0] = 0.0;
    for(int i_g = 0; i_g < 6; i_g++)
    {
      double l5[2] = { c_q2[i_g][1], c_q2[i_g][0] };
      double l35[2][2] = { { c_q0[i_g][1][1], -1 * c_q0[i_g][0][1] }, { -1 * c_q0[i_g][1][0], c_q0[i_g][0][0] } };
      for(int i_d_5 = 0; i_d_5 < 2; i_d_5++)
      {
        for(int i_d_3 = 0; i_d_3 < 2; i_d_3++)
        {
          localTensor[i_r_0] += (CG1[i_r_0][i_g] * c_q1[i_g] + c_q1[i_g] * dt * (l35[i_d_3][i_d_5] / (c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0])) * d_CG1[i_d_3][i_r_0][i_g] * l5[i_d_5]) * (c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0]) * w[i_g];
        };
      };
    };
  };
}

void Mass(double localTensor[3][3], double dt, double c0[3][2])
{
  const double CG1[3][6] = { {  0.09157621, 0.09157621, 0.81684757,
                               0.44594849, 0.44594849, 0.10810302 },
                             {  0.09157621, 0.81684757, 0.09157621,
                               0.44594849, 0.10810302, 0.44594849 },
                             {  0.81684757, 0.09157621, 0.09157621,
                               0.10810302, 0.44594849, 0.44594849 } };
  const double d_CG1[3][6][2] = { { {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. },
                                   {  1., 0. } },

                                  { {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. },
                                   {  0., 1. } },

                                  { { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. },
                                   { -1.,-1. } } };
  const double w[6] = {  0.05497587, 0.05497587, 0.05497587, 0.11169079,
                         0.11169079, 0.11169079 };
  double c_q0[6][2][2];
  for(int i_g = 0; i_g < 6; i_g++)
  {
    for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
    {
      for(int i_d_1 = 0; i_d_1 < 2; i_d_1++)
      {
        c_q0[i_g][i_d_0][i_d_1] = 0.0;
        for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
        {
          c_q0[i_g][i_d_0][i_d_1] += c0[i_r_0][i_d_0] * d_CG1[i_r_0][i_g][i_d_1];
        };
      };
    };
  };
  for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
  {
    for(int i_r_1 = 0; i_r_1 < 3; i_r_1++)
    {
      localTensor[i_r_0][i_r_1] = 0.0;
      for(int i_g = 0; i_g < 6; i_g++)
      {
        localTensor[i_r_0][i_r_1] += CG1[i_r_0][i_g] * CG1[i_r_1][i_g] * (c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0]) * w[i_g];
      };
    };
  };
}



