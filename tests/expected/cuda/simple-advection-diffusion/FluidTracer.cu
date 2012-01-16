// Generated by the Manycore Form Compiler.
// https://github.com/gmarkall/manycore_form_compiler


#include "cudastatic.hpp"
#include "cudastate.hpp"
double* localVector;
double* localMatrix;
double* globalVector;
double* globalMatrix;
double* solutionVector;
int* Tracer_findrm;
int Tracer_findrm_size;
int* Tracer_colm;
int Tracer_colm_size;
int* t_adv_findrm;
int t_adv_findrm_size;
int* t_adv_colm;
int t_adv_colm_size;


__global__ void A(int n_ele, double* localTensor, double dt, double* c0)
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
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    for(int i_g = 0; i_g < 6; i_g++)
    {
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        for(int i_d_1 = 0; i_d_1 < 2; i_d_1++)
        {
          c_q0[i_g][i_d_0][i_d_1] = 0.0;
          for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
          {
            c_q0[i_g][i_d_0][i_d_1] += c0[i_ele + n_ele * (i_d_0 + 2 * i_r_0)] * d_CG1[i_r_0][i_g][i_d_1];
          };
        };
      };
    };
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      for(int i_r_1 = 0; i_r_1 < 3; i_r_1++)
      {
        localTensor[i_ele + n_ele * (i_r_0 + 3 * i_r_1)] = 0.0;
        for(int i_g = 0; i_g < 6; i_g++)
        {
          localTensor[i_ele + n_ele * (i_r_0 + 3 * i_r_1)] += CG1[i_r_0][i_g] * CG1[i_r_1][i_g] * (c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0]) * w[i_g];
          for(int i_d_1 = 0; i_d_1 < 2; i_d_1++)
          {
            localTensor[i_ele + n_ele * (i_r_0 + 3 * i_r_1)] += -1 * 0.5 * d_CG1[i_d_1][i_r_0][i_g] * d_CG1[i_d_1][i_r_1][i_g] * 0.1 * -1 * dt * (c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0]) * w[i_g];
          };
        };
      };
    };
  };
}

__global__ void d(int n_ele, double* localTensor, double dt, double* c0)
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
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    for(int i_g = 0; i_g < 6; i_g++)
    {
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        for(int i_d_1 = 0; i_d_1 < 2; i_d_1++)
        {
          c_q0[i_g][i_d_0][i_d_1] = 0.0;
          for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
          {
            c_q0[i_g][i_d_0][i_d_1] += c0[i_ele + n_ele * (i_d_0 + 2 * i_r_0)] * d_CG1[i_r_0][i_g][i_d_1];
          };
        };
      };
    };
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      for(int i_r_1 = 0; i_r_1 < 3; i_r_1++)
      {
        localTensor[i_ele + n_ele * (i_r_0 + 3 * i_r_1)] = 0.0;
        for(int i_g = 0; i_g < 6; i_g++)
        {
          for(int i_d_1 = 0; i_d_1 < 2; i_d_1++)
          {
            localTensor[i_ele + n_ele * (i_r_0 + 3 * i_r_1)] += d_CG1[i_d_1][i_r_0][i_g] * d_CG1[i_d_1][i_r_1][i_g] * 0.1 * -1 * dt * (c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0]) * w[i_g];
          };
        };
      };
    };
  };
}

__global__ void M(int n_ele, double* localTensor, double dt, double* c0)
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
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    for(int i_g = 0; i_g < 6; i_g++)
    {
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        for(int i_d_1 = 0; i_d_1 < 2; i_d_1++)
        {
          c_q0[i_g][i_d_0][i_d_1] = 0.0;
          for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
          {
            c_q0[i_g][i_d_0][i_d_1] += c0[i_ele + n_ele * (i_d_0 + 2 * i_r_0)] * d_CG1[i_r_0][i_g][i_d_1];
          };
        };
      };
    };
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      for(int i_r_1 = 0; i_r_1 < 3; i_r_1++)
      {
        localTensor[i_ele + n_ele * (i_r_0 + 3 * i_r_1)] = 0.0;
        for(int i_g = 0; i_g < 6; i_g++)
        {
          localTensor[i_ele + n_ele * (i_r_0 + 3 * i_r_1)] += CG1[i_r_0][i_g] * CG1[i_r_1][i_g] * (c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0]) * w[i_g];
        };
      };
    };
  };
}

__global__ void diff_rhs(int n_ele, double* localTensor, double dt, double* c0, double* c1)
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
  double c_q1[6];
  double d_c_q1[6][2];
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    for(int i_g = 0; i_g < 6; i_g++)
    {
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        for(int i_d_1 = 0; i_d_1 < 2; i_d_1++)
        {
          c_q0[i_g][i_d_0][i_d_1] = 0.0;
          for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
          {
            c_q0[i_g][i_d_0][i_d_1] += c0[i_ele + n_ele * (i_d_0 + 2 * i_r_0)] * d_CG1[i_r_0][i_g][i_d_1];
          };
        };
      };
      c_q1[i_g] = 0.0;
      for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
      {
        c_q1[i_g] += c1[i_ele + n_ele * i_r_0] * CG1[i_r_0][i_g];
      };
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        d_c_q1[i_g][i_d_0] = 0.0;
        for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
        {
          d_c_q1[i_g][i_d_0] += c1[i_ele + n_ele * i_r_0] * d_CG1[i_r_0][i_g][i_d_0];
        };
      };
    };
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      localTensor[i_ele + n_ele * i_r_0] = 0.0;
      for(int i_g = 0; i_g < 6; i_g++)
      {
        localTensor[i_ele + n_ele * i_r_0] += CG1[i_r_0][i_g] * c_q1[i_g] * (c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0]) * w[i_g];
        for(int i_d_1 = 0; i_d_1 < 2; i_d_1++)
        {
          localTensor[i_ele + n_ele * i_r_0] += 0.5 * d_CG1[i_d_1][i_r_0][i_g] * d_c_q1[i_d_1][i_g] * 0.1 * -1 * dt * (c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0]) * w[i_g];
        };
      };
    };
  };
}

__global__ void adv_rhs(int n_ele, double* localTensor, double dt, double* c0, double* c1, double* c2)
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
  double c_q2[6][2];
  double c_q0[6][2][2];
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    for(int i_g = 0; i_g < 6; i_g++)
    {
      c_q1[i_g] = 0.0;
      for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
      {
        c_q1[i_g] += c1[i_ele + n_ele * i_r_0] * CG1[i_r_0][i_g];
      };
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        c_q2[i_g][i_d_0] = 0.0;
        for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
        {
          c_q2[i_g][i_d_0] += c2[i_ele + n_ele * (i_d_0 + 2 * i_r_0)] * CG1[i_r_0][i_g];
        };
      };
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        for(int i_d_1 = 0; i_d_1 < 2; i_d_1++)
        {
          c_q0[i_g][i_d_0][i_d_1] = 0.0;
          for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
          {
            c_q0[i_g][i_d_0][i_d_1] += c0[i_ele + n_ele * (i_d_0 + 2 * i_r_0)] * d_CG1[i_r_0][i_g][i_d_1];
          };
        };
      };
    };
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      localTensor[i_ele + n_ele * i_r_0] = 0.0;
      for(int i_g = 0; i_g < 6; i_g++)
      {
        for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
        {
          localTensor[i_ele + n_ele * i_r_0] += (CG1[i_r_0][i_g] * c_q1[i_g] + c_q1[i_g] * dt * c_q2[i_g][i_d_0] * d_CG1[i_d_0][i_r_0][i_g]) * (c_q0[i_g][0][0] * c_q0[i_g][1][1] + -1 * c_q0[i_g][0][1] * c_q0[i_g][1][0]) * w[i_g];
        };
      };
    };
  };
}

StateHolder* state;
extern "C" void initialise_gpu_()
{
  state = new StateHolder();
  state->initialise();
  state->extractField("Velocity", 1);
  state->extractField("Coordinate", 1);
  state->extractField("Tracer", 0);
  state->allocateAllGPUMemory();
  state->transferAllFields();
  int numEle = state->getNumEle();
  int numNodes = state->getNumNodes();
  state->insertTemporaryField("t_adv", "Tracer");
  CsrSparsity* t_adv_sparsity = state->getSparsity("t_adv");
  t_adv_colm = t_adv_sparsity->getCudaColm();
  t_adv_findrm = t_adv_sparsity->getCudaFindrm();
  t_adv_colm_size = t_adv_sparsity->getSizeColm();
  t_adv_findrm_size = t_adv_sparsity->getSizeFindrm();
  CsrSparsity* Tracer_sparsity = state->getSparsity("Tracer");
  Tracer_colm = Tracer_sparsity->getCudaColm();
  Tracer_findrm = Tracer_sparsity->getCudaFindrm();
  Tracer_colm_size = Tracer_sparsity->getSizeColm();
  Tracer_findrm_size = Tracer_sparsity->getSizeFindrm();
  int numValsPerNode = state->getValsPerNode("Tracer");
  int numVectorEntries = state->getNodesPerEle("Tracer");
  numVectorEntries = numVectorEntries * numValsPerNode;
  int numMatrixEntries = numVectorEntries * numVectorEntries;
  cudaMalloc((void**)(&localVector), sizeof(double) * numEle * numVectorEntries);
  cudaMalloc((void**)(&localMatrix), sizeof(double) * numEle * numMatrixEntries);
  cudaMalloc((void**)(&globalVector), sizeof(double) * numNodes * numValsPerNode);
  cudaMalloc((void**)(&globalMatrix), sizeof(double) * Tracer_colm_size);
  cudaMalloc((void**)(&solutionVector), sizeof(double) * numNodes * numValsPerNode);
}

extern "C" void finalise_gpu_()
{
  delete state;
}

extern "C" void run_model_(double* dt_pointer)
{
  double dt = *dt_pointer;
  int numEle = state->getNumEle();
  int numNodes = state->getNumNodes();
  int* eleNodes = state->getEleNodes();
  int nodesPerEle = state->getNodesPerEle("Coordinate");
  int blockXDim = 64;
  int gridXDim = 128;
  double* CoordinateCoeff = state->getElementValue("Coordinate");
  M<<<gridXDim,blockXDim>>>(numEle, localMatrix, dt, CoordinateCoeff);
  double* TracerCoeff = state->getElementValue("Tracer");
  double* VelocityCoeff = state->getElementValue("Velocity");
  adv_rhs<<<gridXDim,blockXDim>>>(numEle, localVector, dt, CoordinateCoeff, TracerCoeff, VelocityCoeff);
  cudaMemset(globalMatrix, 0, sizeof(double) * t_adv_colm_size);
  cudaMemset(globalVector, 0, sizeof(double) * state->getValsPerNode("t_adv") * numNodes);
  matrix_addto<<<gridXDim,blockXDim>>>(t_adv_findrm, t_adv_colm, globalMatrix, eleNodes, localMatrix, numEle, nodesPerEle);
  vector_addto<<<gridXDim,blockXDim>>>(globalVector, eleNodes, localVector, numEle, nodesPerEle);
  cg_solve(t_adv_findrm, t_adv_findrm_size, t_adv_colm, t_adv_colm_size, globalMatrix, globalVector, numNodes, solutionVector);
  double* t_advCoeff = state->getElementValue("t_adv");
  expand_data<<<gridXDim,blockXDim>>>(t_advCoeff, solutionVector, eleNodes, numEle, state->getValsPerNode("t_adv"), nodesPerEle);
  A<<<gridXDim,blockXDim>>>(numEle, localMatrix, dt, CoordinateCoeff);
  diff_rhs<<<gridXDim,blockXDim>>>(numEle, localVector, dt, CoordinateCoeff, t_advCoeff);
  cudaMemset(globalMatrix, 0, sizeof(double) * Tracer_colm_size);
  cudaMemset(globalVector, 0, sizeof(double) * state->getValsPerNode("Tracer") * numNodes);
  matrix_addto<<<gridXDim,blockXDim>>>(Tracer_findrm, Tracer_colm, globalMatrix, eleNodes, localMatrix, numEle, nodesPerEle);
  vector_addto<<<gridXDim,blockXDim>>>(globalVector, eleNodes, localVector, numEle, nodesPerEle);
  cg_solve(Tracer_findrm, Tracer_findrm_size, Tracer_colm, Tracer_colm_size, globalMatrix, globalVector, numNodes, solutionVector);
  expand_data<<<gridXDim,blockXDim>>>(TracerCoeff, solutionVector, eleNodes, numEle, state->getValsPerNode("Tracer"), nodesPerEle);
  state->returnFieldToHost("Tracer");
}



