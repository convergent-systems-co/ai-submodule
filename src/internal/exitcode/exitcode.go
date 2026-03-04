package exitcode

const (
	AutoMerge           = 0
	Block               = 1
	HumanReviewRequired = 2
	AutoRemediate       = 3
)

// ExitError represents a governance decision as a process exit code.
type ExitError struct {
	Code    int
	Message string
}

func (e *ExitError) Error() string { return e.Message }
