# Taken from https://stackoverflow.com/questions/38230794/how-to-write-fftshift-and-ifftshift-in-r
# Contributed by StackOverflow user "rayryeng" (https://stackoverflow.com/users/3250829/rayryeng)

# Imagine that your input 2D matrix is split up into quadrants. Quadrant #1 is
# at the top left, quadrant #2 is at the top right, quadrant #3 is at the
# bottom right and quadrant #4 is at the bottom left. For 2D matrices, fftshift
# swaps the first and third quadrants and second and fourth quadrants by
# default. You can override this behaviour where you can simply perform
# fftshift on one dimension separately. If you do this, you are swapping what
# are known as half spaces. If you specified to swap along the rows (i.e.
# dimension 1), then the top half of the matrix gets swapped with the bottom
# half. If you specified to swap along the columns (i.e. dimension 2), then the
# right half gets swapped with the left half.  Using fftshift by default chains
# the swapping of dimensions 1 and dimensions 2 in sequence. If you have an
# even sized matrix where the rows and columns are even, then it's very
# unambiguous to cut the matrix into the four portions and do the swapping.
# However, if the matrix is odd sized, it depends on which language you're
# looking at. In MATLAB and Python numpy for instance, where to perform the
# switching is defined as (r,c) = ceil(rows/2), ceil(cols/2) where rows and
# cols are the rows and columns of the matrix. r and c are the row and column
# of where the swapping takes place.
fftshift <- function(input_matrix, dim = -1) {

    rows <- dim(input_matrix)[1]    
    cols <- dim(input_matrix)[2]    

    swap_up_down <- function(input_matrix) {
        rows_half <- ceiling(rows/2)
        return(rbind(input_matrix[((rows_half+1):rows), (1:cols)], input_matrix[(1:rows_half), (1:cols)]))
    }

    swap_left_right <- function(input_matrix) {
        cols_half <- ceiling(cols/2)
        return(cbind(input_matrix[1:rows, ((cols_half+1):cols)], input_matrix[1:rows, 1:cols_half]))
    }

    if (dim == -1) {
        input_matrix <- swap_up_down(input_matrix)
        return(swap_left_right(input_matrix))
    }
    else if (dim == 1) {
        return(swap_up_down(input_matrix))
    }
    else if (dim == 2) {
        return(swap_left_right(input_matrix))
    }
    else {
        stop("Invalid dimension parameter")
    }
}

# For ifftshift you simply reverse the actions done on fftshift. Therefore, the
# default action is to swap dimensions 2 then dimensions 1. However, you have
# to redefine where the centre of switching is for matrices of odd dimensions.
# Instead of ceil, you must use floor because this precisely determines where
# the half spaces were after fftshift was performed and you are now undoing
# what was done on the original matrix. Therefore, the new centre of switching
# is (r,c) = floor(rows/2), floor(cols/2). Other than that, the logic to swap
# among a single dimension is the same - just that the centre of switching has
# now changed.
ifftshift <- function(input_matrix, dim = -1) {

    rows <- dim(input_matrix)[1]    
    cols <- dim(input_matrix)[2]    

    swap_up_down <- function(input_matrix) {
        rows_half <- floor(rows/2)
        return(rbind(input_matrix[((rows_half+1):rows), (1:cols)], input_matrix[(1:rows_half), (1:cols)]))
    }

    swap_left_right <- function(input_matrix) {
        cols_half <- floor(cols/2)
        return(cbind(input_matrix[1:rows, ((cols_half+1):cols)], input_matrix[1:rows, 1:cols_half]))
    }

    if (dim == -1) {
        input_matrix <- swap_left_right(input_matrix)
        return(swap_up_down(input_matrix))
    }
    else if (dim == 1) {
        return(swap_up_down(input_matrix))
    }
    else if (dim == 2) {
        return(swap_left_right(input_matrix))
    }
    else {
        stop("Invalid dimension parameter")
    }

}
