// Generated by the Manycore Form Compiler.
// https://github.com/gmarkall/manycore_form_compiler




void Mass(double localTensor[3][3], double dt)
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
  const double detwei[6] = {  0.05497587, 0.05497587, 0.05497587,
                              0.11169079, 0.11169079, 0.11169079 };
  for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
  {
    for(int i_r_1 = 0; i_r_1 < 3; i_r_1++)
    {
      localTensor[i_r_0][i_r_1] = 0.0;
      for(int i_g = 0; i_g < 6; i_g++)
      {
        localTensor[i_r_0][i_r_1] += CG1[i_r_0][i_g] * CG1[i_r_1][i_g] * detwei[i_g];
      };
    };
  };
}

void rhs(double localTensor[3], double dt, double c0[3], double c1[3][2])
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
  const double detwei[6] = {  0.05497587, 0.05497587, 0.05497587,
                              0.11169079, 0.11169079, 0.11169079 };
  double c_q0[6];
  double c_q1[6][2];
  for(int i_g = 0; i_g < 6; i_g++)
  {
    c_q0[i_g] = 0.0;
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      c_q0[i_g] += c0[i_r_0] * CG1[i_r_0][i_g];
    };
    for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
    {
      c_q1[i_g][i_d_0] = 0.0;
      for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
      {
        c_q1[i_g][i_d_0] += c1[i_r_0][i_d_0] * CG1[i_r_0][i_g];
      };
    };
  };
  for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
  {
    localTensor[i_r_0] = 0.0;
    for(int i_g = 0; i_g < 6; i_g++)
    {
      localTensor[i_r_0] += CG1[i_r_0][i_g] * c_q0[i_g] * detwei[i_g];
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        localTensor[i_r_0] += c_q0[i_g] * dt * c_q1[i_g][i_d_0] * d_CG1[i_d_0][i_g][i_r_0] * detwei[i_g];
      };
    };
  };
}



